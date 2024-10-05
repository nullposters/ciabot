# Base image with .NET runtime
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
WORKDIR /app

# Build stage with SDK
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
ARG BUILD_CONFIGURATION=Release
WORKDIR /src

# Copy the project files and restore dependencies
COPY ["CIA.Net.Public.Bot/CIA.Net.Public.Bot.csproj", "CIA.Net.Public.Bot/"]


# Restore the project
RUN dotnet restore "./CIA.Net.Public.Bot/CIA.Net.Public.Bot.csproj"

# Copy the entire source code and build the application
COPY . .
WORKDIR "/src/CIA.Net.Public.Bot"
RUN dotnet build "./CIA.Net.Public.Bot.csproj" -c $BUILD_CONFIGURATION -o /app/build

# Publish the application
FROM build AS publish
ARG BUILD_CONFIGURATION=Release
RUN dotnet publish "./CIA.Net.Public.Bot.csproj" -c $BUILD_CONFIGURATION -o /app/publish /p:UseAppHost=false

# Final runtime image with published app
FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .

# Set user to app for running the application
USER app

ENTRYPOINT ["dotnet", "CIA.Net.Public.Bot.dll"]
