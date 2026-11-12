package com.saferent.api;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.web.server.ServerHttpSecurity;
import org.springframework.security.web.server.SecurityWebFilterChain;
@Configuration
public class SecurityConfig {
 @Bean SecurityWebFilterChain security(ServerHttpSecurity http,
  @Value("${saferent.local-dev-no-auth:false}") boolean localDev) {
  http.csrf(ServerHttpSecurity.CsrfSpec::disable);
  if(localDev) { http.authorizeExchange(ex -> ex.anyExchange().permitAll()); }
  else { http.authorizeExchange(ex -> ex.pathMatchers("/actuator/health").permitAll().anyExchange().authenticated())
   .oauth2ResourceServer(oauth -> oauth.jwt(jwt -> {})); }
  return http.build();
 }
}
