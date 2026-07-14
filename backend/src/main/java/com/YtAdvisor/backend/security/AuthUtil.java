package com.YtAdvisor.backend.security;

import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.server.ResponseStatusException;

public class AuthUtil {

    public static UUID getCurrentUserId() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || authentication.getPrincipal() == null || "anonymousUser".equals(authentication.getPrincipal())) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Not authenticated");
        }
        Object principal = authentication.getPrincipal();
        try {
            return UUID.fromString(principal.toString());
        } catch (IllegalArgumentException e) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Invalid authentication principal");
        }
    }
}
