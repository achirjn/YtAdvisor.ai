package com.YtAdvisor.backend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class BackendApplication {

	static {
		try {
			java.nio.file.Path envPath = java.nio.file.Paths.get(".env");
			if (!java.nio.file.Files.exists(envPath)) {
				envPath = java.nio.file.Paths.get("..", ".env");
			}
			if (java.nio.file.Files.exists(envPath)) {
				System.out.println("[env-loader] Found .env file at: " + envPath.toAbsolutePath());
				java.nio.file.Files.lines(envPath)
					.map(String::trim)
					.filter(line -> !line.isEmpty() && !line.startsWith("#"))
					.forEach(line -> {
						int eqIdx = line.indexOf('=');
						if (eqIdx > 0) {
							String key = line.substring(0, eqIdx).trim();
							String value = line.substring(eqIdx + 1).trim();
							if ((value.startsWith("\"") && value.endsWith("\"")) || (value.startsWith("'") && value.endsWith("'"))) {
								value = value.substring(1, value.length() - 1);
							}
							
							// Map key as-is
							if (System.getenv(key) == null && System.getProperty(key) == null) {
								System.setProperty(key, value);
								System.out.println("[env-loader] Loaded " + key + " (length: " + value.length() + ")");
							}
							
							// Relaxed binding mapper (translate dot/dash notation keys to uppercase-underscore)
							String envKey = key.replace('.', '_').replace('-', '_').toUpperCase();
							if (!envKey.equals(key) && System.getenv(envKey) == null && System.getProperty(envKey) == null) {
								System.setProperty(envKey, value);
								System.out.println("[env-loader] Relaxed-mapped " + envKey + " from " + key + " (length: " + value.length() + ")");
							}
						}
					});
			} else {
				System.out.println("[env-loader] No .env file found. Sourcing solely from system environment.");
			}
		} catch (Exception e) {
			System.err.println("[env-loader] Failed to load .env file: " + e.getMessage());
		}
	}

	public static void main(String[] args) {
		SpringApplication.run(BackendApplication.class, args);
	}

}
