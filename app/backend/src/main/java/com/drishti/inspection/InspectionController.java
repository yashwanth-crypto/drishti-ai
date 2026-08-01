package com.drishti.inspection;

import org.springframework.http.MediaType;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class InspectionController {

    private final InspectionService service;

    public InspectionController(InspectionService service) {
        this.service = service;
    }

    @PostMapping(value = "/inspections", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Inspection create(@RequestPart("image") MultipartFile image,
                             @RequestParam(value = "partId", required = false) String partId) throws IOException {
        return service.inspect(image, partId);
    }

    @GetMapping("/inspections")
    public List<Inspection> list(@RequestParam(defaultValue = "all") String filter) {
        return service.list(filter);
    }

    @GetMapping(value = "/inspections/{id}/image", produces = MediaType.IMAGE_JPEG_VALUE)
    public byte[] image(@PathVariable Long id) throws IOException {
        return service.imageFor(id);
    }

    @PatchMapping("/inspections/{id}/feedback")
    public Inspection feedback(@PathVariable Long id,
                               @RequestBody Map<String, String> body,
                               Authentication authentication) {
        return service.recordFeedback(id, body.get("operatorVerdict"), authentication.getName());
    }

    @GetMapping("/kpis")
    public InspectionService.Kpis kpis() {
        return service.kpis();
    }
}
