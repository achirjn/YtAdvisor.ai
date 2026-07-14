package com.YtAdvisor.backend.controllers;

import java.util.UUID;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import com.YtAdvisor.backend.dto.AnalysisRequestDto;
import com.YtAdvisor.backend.entities.User;
import com.YtAdvisor.backend.repositories.UserRepository;
import com.YtAdvisor.backend.security.AuthUtil;
import com.YtAdvisor.backend.services.AnalysisService;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/api/analysis")
@RequiredArgsConstructor
public class AnalysisController {

    private final AnalysisService analysisService;
    private final UserRepository userRepository;
    private final ObjectMapper objectMapper;

    @PostMapping(produces = "application/json")
    public ResponseEntity<String> analyse(@Valid @RequestBody AnalysisRequestDto dto) {
        System.out.println("Received analysis request: " + dto);

        UUID userId = AuthUtil.getCurrentUserId();
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED, "User not found"));

        JsonNode result = analysisService.analyse(user.getId(), dto.getVideoIdea());

        try {
            return ResponseEntity.ok(objectMapper.writeValueAsString(result));
        } catch (Exception e) {
            throw new RuntimeException("Failed to serialize response", e);
        }
    }
}
