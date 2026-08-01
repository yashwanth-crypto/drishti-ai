package com.drishti.seed;

import com.drishti.auth.Role;
import com.drishti.auth.User;
import com.drishti.auth.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

/**
 * Creates one OWNER and one OPERATOR on first run so a fresh install can be
 * logged into. Only ever runs against an empty users table, and these are
 * obvious development credentials -- set SEED_USERS=false and register real
 * accounts before putting this anywhere that matters.
 */
@Component
public class UserSeeder implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(UserSeeder.class);

    private final UserRepository users;
    private final PasswordEncoder encoder;
    private final boolean enabled;

    public UserSeeder(UserRepository users,
                      PasswordEncoder encoder,
                      @Value("${drishti.seed-users}") boolean enabled) {
        this.users = users;
        this.encoder = encoder;
        this.enabled = enabled;
    }

    @Override
    public void run(String... args) {
        if (!enabled || users.count() > 0) return;

        create("owner", "drishti-owner", Role.OWNER);
        create("operator", "drishti-operator", Role.OPERATOR);
        log.warn("Seeded development accounts owner/operator -- change or disable "
                + "(SEED_USERS=false) before any real deployment");
    }

    private void create(String username, String password, Role role) {
        User user = new User();
        user.setUsername(username);
        user.setPasswordHash(encoder.encode(password));
        user.setRole(role);
        users.save(user);
    }
}
