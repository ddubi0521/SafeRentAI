package com.saferent.api;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.*;
import org.springframework.http.codec.multipart.FilePart;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.util.MultiValueMap;
import org.springframework.util.LinkedMultiValueMap;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/tools/safe-rent")
public class AnalysisController {
 private final WebClient client;
 private final String token;
 public AnalysisController(WebClient.Builder builder,
  @Value("${saferent.core-url}") String url, @Value("${saferent.core-token}") String token) {
  this.client=builder.baseUrl(url).build(); this.token=token;
 }
 @GetMapping("/health")
 public Mono<ResponseEntity<?>> health() {
  return Mono.just(ResponseEntity.ok(java.util.Map.<String, Object>of("data",java.util.Map.of("status","UP"))));
 }
 @PostMapping(value="/analyze",consumes=MediaType.MULTIPART_FORM_DATA_VALUE)
 public Mono<ResponseEntity<java.util.Map<String, Object>>> analyze(@RequestPart("file") FilePart file) {
  if (!file.filename().toLowerCase().endsWith(".pdf")) return Mono.just(ResponseEntity.status(415).body(java.util.Map.of("payload",java.util.Map.of("message","PDF만 지원"))));
  return org.springframework.core.io.buffer.DataBufferUtils.join(file.content(),20*1024*1024)
   .flatMap(buffer -> {
    byte[] bytes=new byte[buffer.readableByteCount()];buffer.read(bytes);
    org.springframework.core.io.buffer.DataBufferUtils.release(buffer);
    ByteArrayResource resource = new ByteArrayResource(bytes) { @Override public String getFilename() {return file.filename();} };
    MultiValueMap<String,Object> parts=new LinkedMultiValueMap<>();parts.add("file",resource);
    return client.post().uri("/internal/analyze")
     .header("X-Core-Token",token).contentType(MediaType.MULTIPART_FORM_DATA)
     .body(BodyInserters.fromMultipartData(parts))
     .retrieve().toEntity(Object.class)
     .map(resp -> ResponseEntity.ok(java.util.Map.<String, Object>of("data",resp.getBody())));
   }).onErrorResume(Exception.class, e -> Mono.just(ResponseEntity.status(502)
    .body(java.util.Map.of("payload",java.util.Map.<String, Object>of("message","분석 서비스 호출에 실패했습니다. 파일·Core 연결을 확인하세요.")))));
 }
}
