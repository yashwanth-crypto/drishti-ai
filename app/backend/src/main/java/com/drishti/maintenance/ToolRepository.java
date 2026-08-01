package com.drishti.maintenance;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

public interface ToolRepository extends JpaRepository<Tool, Long> {
    Optional<Tool> findByToolRef(Integer toolRef);
    List<Tool> findAllByOrderByToolRefAsc();
}
