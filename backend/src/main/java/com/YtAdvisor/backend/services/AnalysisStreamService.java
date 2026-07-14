package com.YtAdvisor.backend.services;

import java.io.IOException;
import java.time.Duration;
import java.time.OffsetDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;

import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import com.YtAdvisor.backend.entities.AnalysisRequest;
import com.YtAdvisor.backend.entities.AnalysisResponse;
import com.YtAdvisor.backend.entities.Channel;
import com.YtAdvisor.backend.entities.DnaSnapshot;
import com.YtAdvisor.backend.entities.User;
import com.YtAdvisor.backend.repositories.AnalysisRequestRepository;
import com.YtAdvisor.backend.repositories.AnalysisResponseRepository;
import com.YtAdvisor.backend.repositories.ChannelRepository;
import com.YtAdvisor.backend.repositories.DnaSnapshotRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import reactor.core.scheduler.Schedulers;

@Service
@RequiredArgsConstructor
@Slf4j
public class AnalysisStreamService {

    private final ChannelRepository channelRepository;
    private final DnaSnapshotRepository dnaSnapshotRepository;
    private final AnalysisRequestRepository analysisRequestRepository;
    private final AnalysisResponseRepository analysisResponseRepository;
    private final WebClient pythonWebClient;
    private final ObjectMapper objectMapper;
    private final TierService tierService;

    /**
     * Tier check + DNA load happen synchronously (on the servlet thread) before this
     * method returns, so ResponseStatusException propagates cleanly to the client.
     * The actual SSE proxy runs asynchronously on the bounded-elastic scheduler.
     */
    public SseEmitter startStream(User user, String videoIdea) {
        // 1. Tier check — throws 429 ResponseStatusException if over limit
        tierService.checkAndConsumeRequest(user);

        // 2. Load creator DNA from the latest reliable snapshot (optional)
        Channel channel = channelRepository.findByUser_Id(user.getId()).orElse(null);
        String creatorDna = null;
        if (channel != null) {
            DnaSnapshot snap = dnaSnapshotRepository
                    .findTopByChannel_IdOrderByCreatedAtDesc(channel.getId())
                    .orElse(null);
            if (snap != null && Boolean.TRUE.equals(snap.getIsReliable())) {
                creatorDna = snap.getDnaSummary();
                log.info("[stream] using DNA snapshot for channel: {}", channel.getYoutubeChannelId());
            }
        }

        // 3. Persist analysis request as PROCESSING
        AnalysisRequest req = new AnalysisRequest();
        req.setUser(user);
        req.setChannel(channel);
        req.setVideoIdea(videoIdea);
        req.setCreatorDnaUsed(creatorDna);
        req.setStatus("PROCESSING");
        final AnalysisRequest savedReq = analysisRequestRepository.save(req);
        final String finalCreatorDna = creatorDna;

        // 4. Build request body for Python
        Map<String, Object> body = new HashMap<>();
        body.put("video_idea", videoIdea);
        if (finalCreatorDna != null) body.put("creator_dna", finalCreatorDna);

        // 5. Create the SseEmitter (300-second timeout — covers full pipeline worst case)
        //    spring.mvc.async.request-timeout is set to -1 so this emitter is the sole authority.
        SseEmitter emitter = new SseEmitter(300_000L);
        AtomicBoolean resultReceived = new AtomicBoolean(false);

        // 6. Subscribe to Python's SSE stream on the bounded-elastic pool
        //    (publishOn ensures JPA saves in callbacks run on a blocking-safe thread)
        pythonWebClient.post()
                .uri("/api/v1/analyze/stream")
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.TEXT_EVENT_STREAM)
                .bodyValue(body)
                .retrieve()
                .bodyToFlux(new ParameterizedTypeReference<ServerSentEvent<String>>() {})
                .publishOn(Schedulers.boundedElastic())
                .subscribe(
                        event -> handleEvent(event, emitter, savedReq, user, resultReceived),
                        error -> {
                            log.error("[stream] Python stream error: {}", error.getMessage());
                            if (!resultReceived.get()) {
                                markFailed(savedReq, error.getMessage());
                            }
                            emitter.completeWithError(error);
                        },
                        emitter::complete
                );

        return emitter;
    }

    // ── Event handler ─────────────────────────────────────────────────────────

    private void handleEvent(ServerSentEvent<String> event,
                             SseEmitter emitter,
                             AnalysisRequest req,
                             User user,
                             AtomicBoolean resultReceived) {
        String type = event.event() != null ? event.event() : "message";
        String data = event.data() != null ? event.data() : "";
        try {
            // Forward every event straight to the frontend
            emitter.send(SseEmitter.event().name(type).data(data));

            if ("result".equals(type)) {
                resultReceived.set(true);
                persistResult(req, data, user);
            } else if ("error".equals(type)) {
                markFailed(req, data);
            }
        } catch (IOException e) {
            log.warn("[stream] emitter send failed (client disconnected?): {}", e.getMessage());
            emitter.completeWithError(e);
        }
    }

    // ── DB persistence helpers ─────────────────────────────────────────────────

    private void persistResult(AnalysisRequest req, String rawJson, User user) {
        try {
            JsonNode rawNode = objectMapper.readTree(rawJson);
            AnalysisResponse resp = new AnalysisResponse();
            resp.setRequest(req);
            resp.setRawResponse(rawJson);
            resp.setFinalVerdict(rawNode.path("verdict").path("final_verdict").asText(null));
            resp.setConfidence(rawNode.path("verdict").path("confidence").asText(null));
            resp.setSmallCreatorVerdict(rawNode.path("market").path("small_creator_verdict").asText(null));
            analysisResponseRepository.save(resp);

            tierService.recordAnalysisRun(user);

            req.setStatus("COMPLETED");
            req.setCompletedAt(OffsetDateTime.now());
            analysisRequestRepository.save(req);

            log.info("[stream] analysis completed and persisted for userId={}", user.getId());
        } catch (Exception e) {
            log.error("[stream] failed to persist result: {}", e.getMessage());
        }
    }

    private void markFailed(AnalysisRequest req, String errorDetail) {
        try {
            req.setStatus("FAILED");
            req.setErrorMessage(errorDetail);
            req.setCompletedAt(OffsetDateTime.now());
            analysisRequestRepository.save(req);
        } catch (Exception e) {
            log.error("[stream] failed to mark request as failed: {}", e.getMessage());
        }
    }
}
