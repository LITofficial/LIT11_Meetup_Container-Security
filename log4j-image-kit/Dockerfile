# Package detection demo only: no server, exploit, or Java application.
FROM maven:3.9-eclipse-temurin-17 AS download
ARG LOG4J_VERSION
RUN mvn -B org.apache.maven.plugins:maven-dependency-plugin:3.8.1:copy -Dartifact=org.apache.logging.log4j:log4j-core:${LOG4J_VERSION} -DoutputDirectory=/out
FROM scratch
COPY --from=download /out/ /demo-libs/
