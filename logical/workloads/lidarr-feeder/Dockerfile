FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
COPY ./src/LidarrFeeder.csproj ./app/
RUN dotnet restore ./app/LidarrFeeder.csproj
COPY ./src ./app
WORKDIR /app
RUN dotnet publish LidarrFeeder.csproj -c Release -o /app/publish

FROM mcr.microsoft.com/dotnet/aspnet:9.0
WORKDIR /app
COPY --from=build /app/publish .
ENTRYPOINT ["dotnet", "LidarrFeeder.dll"]