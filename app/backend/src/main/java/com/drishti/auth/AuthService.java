package com.drishti.auth;

import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class AuthService {

    private final UserRepository users;
    private final PasswordEncoder encoder;
    private final JwtService jwt;

    public AuthService(UserRepository users, PasswordEncoder encoder, JwtService jwt) {
        this.users = users;
        this.encoder = encoder;
        this.jwt = jwt;
    }

    public TokenResponse register(String username, String password, Role role) {
        if (users.existsByUsername(username)) {
            throw new IllegalArgumentException("Username '" + username + "' is taken");
        }
        User user = new User();
        user.setUsername(username);
        user.setPasswordHash(encoder.encode(password));
        user.setRole(role == null ? Role.OPERATOR : role);
        return tokenFor(users.save(user));
    }

    public TokenResponse login(String username, String password) {
        User user = users.findByUsername(username)
                .filter(u -> encoder.matches(password, u.getPasswordHash()))
                // Same message either way, so the response can't be used to
                // discover which usernames exist.
                .orElseThrow(() -> new BadCredentialsException("Invalid username or password"));
        return tokenFor(user);
    }

    private TokenResponse tokenFor(User user) {
        return new TokenResponse(jwt.issue(user), user.getUsername(), user.getRole(), jwt.ttlSeconds());
    }

    public record TokenResponse(String token, String username, Role role, long expiresInSeconds) {}

    /** Distinct from IllegalArgumentException so it can map to 401 rather than 400. */
    public static class BadCredentialsException extends RuntimeException {
        public BadCredentialsException(String message) {
            super(message);
        }
    }
}
