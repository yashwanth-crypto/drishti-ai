package com.drishti.ml;

import org.springframework.http.HttpStatusCode;

/** An error returned by the Python inference service, carrying its status through. */
public class InferenceException extends RuntimeException {

    private final HttpStatusCode status;

    public InferenceException(HttpStatusCode status, String message) {
        super(message);
        this.status = status;
    }

    public HttpStatusCode getStatus() {
        return status;
    }
}
