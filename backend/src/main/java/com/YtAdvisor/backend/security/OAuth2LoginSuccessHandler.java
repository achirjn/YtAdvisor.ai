package com.YtAdvisor.backend.security;

import java.io.IOException;
import java.time.Duration;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseCookie;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.security.web.authentication.SimpleUrlAuthenticationSuccessHandler;
import org.springframework.stereotype.Component;

import com.YtAdvisor.backend.entities.User;
import com.YtAdvisor.backend.repositories.UserRepository;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class OAuth2LoginSuccessHandler extends SimpleUrlAuthenticationSuccessHandler {

    private final UserRepository userRepository;
    private final JwtService jwtService;

    @Value("${app.frontend-url}")
    private String frontendUrl;

    @Value("${app.cookie-secure}")
    private boolean cookieSecure;

    @Override
    public void onAuthenticationSuccess(HttpServletRequest request,
                                        HttpServletResponse response,
                                        Authentication authentication) throws IOException {

        OAuth2User oAuth2User = (OAuth2User) authentication.getPrincipal();

        String googleId = oAuth2User.getAttribute("sub");
        String email    = oAuth2User.getAttribute("email");
        String name     = oAuth2User.getAttribute("name");
        String picture  = oAuth2User.getAttribute("picture");

        User user = userRepository.findByGoogleId(googleId)
                .orElseGet(() -> {
                    User newUser = new User();
                    newUser.setGoogleId(googleId);
                    newUser.setEmail(email);
                    newUser.setName(name);
                    newUser.setPictureUrl(picture);
                    return userRepository.save(newUser);
                });

        // Keep name and picture in sync with Google
        boolean dirty = false;
        if (name != null && !name.equals(user.getName())) {
            user.setName(name);
            dirty = true;
        }
        if (picture != null && !picture.equals(user.getPictureUrl())) {
            user.setPictureUrl(picture);
            dirty = true;
        }
        if (dirty) {
            userRepository.save(user);
        }

        String token = jwtService.generateToken(user.getId(), user.getEmail());

        ResponseCookie cookie = ResponseCookie.from("auth_token", token)
                .httpOnly(true)
                .secure(cookieSecure)
                .sameSite("None")
                .path("/")
                .maxAge(Duration.ofDays(1))
                .build();
        
        response.addHeader(HttpHeaders.SET_COOKIE, cookie.toString());
        getRedirectStrategy().sendRedirect(request, response, "/post-login");
    }
}
