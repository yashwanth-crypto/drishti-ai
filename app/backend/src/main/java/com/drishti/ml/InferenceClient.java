package com.drishti.ml;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.MediaType;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.ClientResponse;
import org.springframework.web.reactive.function.client.ExchangeFilterFunction;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Calls the Python inference service that wraps the trained models. */
@Component
public class InferenceClient {

    private final WebClient client;

    public InferenceClient(@Value("${drishti.inference-url}") String baseUrl) {
        this.client = WebClient.builder()
                .baseUrl(baseUrl)
                .codecs(c -> c.defaultCodecs().maxInMemorySize(16 * 1024 * 1024))
                .filter(ExchangeFilterFunction.ofResponseProcessor(InferenceClient::translateErrors))
                .build();
    }

    /** Surfaces the inference service's own status and message instead of a blanket 500. */
    private static Mono<ClientResponse> translateErrors(ClientResponse response) {
        if (!response.statusCode().isError()) {
            return Mono.just(response);
        }
        return response.bodyToMono(String.class).defaultIfEmpty("")
                .flatMap(body -> Mono.error(new InferenceException(response.statusCode(), body)));
    }

    public VisionResult predictVision(byte[] imageBytes, String filename) {
        MultipartBodyBuilder body = new MultipartBodyBuilder();
        body.part("image", new ByteArrayResource(imageBytes) {
            @Override
            public String getFilename() {
                return filename;
            }
        }).contentType(MediaType.IMAGE_JPEG);

        return client.post()
                .uri("/predict/vision")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(BodyInserters.fromMultipartData(body.build()))
                .retrieve()
                .bodyToMono(VisionResult.class)
                .block(Duration.ofSeconds(60));
    }

    public MaintenanceResult predictMaintenance(Map<String, Double> features) {
        return client.post()
                .uri("/predict/maintenance")
                .bodyValue(Map.of("features", features))
                .retrieve()
                .bodyToMono(MaintenanceResult.class)
                .block(Duration.ofSeconds(30));
    }

    /** A null history tells the inference service to use its recorded weekly series. */
    public ForecastResponse forecast(String category, List<Map<String, Object>> history, int horizon) {
        Map<String, Object> body = new HashMap<>();
        body.put("category", category);
        body.put("horizon", horizon);
        if (history != null) {
            body.put("history", history);
        }
        return client.post()
                .uri("/predict/forecast")
                .bodyValue(body)
                .retrieve()
                .bodyToMono(ForecastResponse.class)
                .block(Duration.ofSeconds(60));
    }

    public record VisionResult(String pass_fail, String defect_type, Double confidence, Double inference_ms) {}

    public record MaintenanceResult(Double predicted_rul, Boolean wear_alert) {}

    public record ForecastPointDto(String week, Double predicted_demand, Double lower, Double upper) {}

    public record ForecastResponse(String category, List<ForecastPointDto> forecast) {}
}
