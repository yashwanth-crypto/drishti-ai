package com.drishti.inspection;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface InspectionRepository extends JpaRepository<Inspection, Long> {
    List<Inspection> findAllByOrderByTimestampDesc();
    List<Inspection> findByPassFailOrderByTimestampDesc(String passFail);
    long countByPassFail(String passFail);
}
