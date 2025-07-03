plugins {
    id("java")
}

group = "com.example.java"
version = "1.0.0"

java {
    sourceCompatibility = JavaVersion.VERSION_21
    targetCompatibility = JavaVersion.VERSION_21
}

repositories {
    mavenCentral()
}

dependencies {
    implementation(libs.json)
    implementation(libs.logback.classic)
    implementation(libs.milo.sdk.client)
    implementation(libs.slf4j.api)
}
