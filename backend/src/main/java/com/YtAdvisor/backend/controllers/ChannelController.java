package com.YtAdvisor.backend.controllers;

import java.util.Map;
import java.util.UUID;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import com.YtAdvisor.backend.security.AuthUtil;

import com.YtAdvisor.backend.dto.ChannelConnectDto;
import com.YtAdvisor.backend.dto.ChannelStatusResponse;
import com.YtAdvisor.backend.entities.Channel;
import com.YtAdvisor.backend.entities.PipelineJob;
import com.YtAdvisor.backend.repositories.ChannelRepository;
import com.YtAdvisor.backend.repositories.PipelineJobRepository;
import com.YtAdvisor.backend.services.ChannelService;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/api/channel")
@RequiredArgsConstructor
public class ChannelController {

    private final ChannelService channelService;
    private final ChannelRepository channelRepository;
    private final PipelineJobRepository pipelineJobRepository;

    @PostMapping("/connect")
    @ResponseStatus(HttpStatus.ACCEPTED)
    public Map<String, Object> connect(@Valid @RequestBody ChannelConnectDto dto) {
        UUID userId = AuthUtil.getCurrentUserId();

        Channel channel = channelService.connectChannel(userId, dto.getChannelInput());

        return Map.of(
                "channelId", channel.getId().toString(),
                "youtubeChannelId", channel.getYoutubeChannelId(),
                "channelTitle", channel.getChannelTitle() != null ? channel.getChannelTitle() : "",
                "phase", channel.getPipelineJob() != null
                        ? channel.getPipelineJob().getPhase()
                        : "BOOTSTRAPPING"
        );
    }

    @GetMapping("/status")
    public ChannelStatusResponse status() {
        UUID userId = AuthUtil.getCurrentUserId();

        Channel channel = channelRepository.findByUser_Id(userId)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND, "No channel connected for this user"));

        PipelineJob job = pipelineJobRepository
                .findByChannel_Id(channel.getId())
                .orElse(null);

        return ChannelStatusResponse.builder()
                .youtubeChannelId(channel.getYoutubeChannelId())
                .channelTitle(channel.getChannelTitle())
                .phase(job != null ? job.getPhase() : "NOT_STARTED")
                .videosProcessed(job != null && job.getVideosProcessed() != null
                        ? job.getVideosProcessed() : 0)
                .totalVideosOnChannel(job != null && job.getTotalVideosOnChannel() != null
                        ? job.getTotalVideosOnChannel() : 0)
                .isReliable(job != null && Boolean.TRUE.equals(job.getIsReliable()))
                .build();
    }
}
