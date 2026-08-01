package com.drishti.auth;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import jakarta.validation.Valid;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService auth;

    public AuthController(AuthService auth) {
        this.auth = auth;
    }

    @PostMapping("/register")
    public AuthService.TokenResponse register(@Valid @RequestBody RegisterRequest request) {
        return auth.register(request.username(), request.password(), request.role());
    }

    @PostMapping("/login")
    public AuthService.TokenResponse login(@Valid @RequestBody LoginRequest request) {
        return auth.login(request.username(), request.password());
    }

    /** Who the current token belongs to — lets the UI restore a session on reload. */
    @GetMapping("/me")
    public Map<String, String> me(Authentication authentication) {
        return Map.of(
                "username", authentication.getName(),
                "role", authentication.getAuthorities().iterator().next()
                        .getAuthority().replaceFirst("^ROLE_", ""));
    }

    public record RegisterRequest(
            @NotBlank String username,
            @NotBlank @Size(min = 8, message = "Password must be at least 8 characters") String password,
            Role role) {}

    public record LoginRequest(@NotBlank String username, @NotBlank String password) {}
}
