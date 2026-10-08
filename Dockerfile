FROM astrocrpublic.azurecr.io/runtime:3.1-13

USER root
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-17-jdk-headless && apt-get clean

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

USER astro