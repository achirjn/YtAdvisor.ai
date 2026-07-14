package com.YtAdvisor.backend.controllers;

import java.io.IOException;
import java.util.Arrays;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import com.YtAdvisor.backend.entities.User;
import com.YtAdvisor.backend.repositories.UserRepository;
import com.YtAdvisor.backend.security.AuthUtil;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

@RestController
public class SecurityController {

    private UserRepository userRepository;

    @Value("${app.frontend-url}")
    private String frontendUrl;

    public SecurityController(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @GetMapping("/api/user/me")
    public Map<String, Object> me() {
        UUID userId = AuthUtil.getCurrentUserId();

        Optional<User> userOpt = userRepository.findById(userId);
        User user = userOpt.orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED, "User not found in database"));

        return Map.of(
                "id", user.getId(),
                "email", user.getEmail(),
                "name", user.getName(),
                "tier", user.getTier());
    }

    @GetMapping("/post-login")
    public void postLogin(HttpServletResponse response) throws IOException {
        response.sendRedirect(frontendUrl + "/pricing");
    }

    @GetMapping("/test")
    @ResponseBody
    public String test(HttpServletRequest request) {
        return Arrays.toString(request.getCookies());
    }
}
