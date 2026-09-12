using System;

public static class AppEnvironment
{
    public static string LidarrApiKey =>
        Environment.GetEnvironmentVariable("LIDARR_API_KEY") ?? throw new InvalidOperationException("LIDARR_API_KEY is not set.");
    public static string LidarrUrl =>
        Environment.GetEnvironmentVariable("LIDARR_URL") ?? throw new InvalidOperationException("LIDARR_URL is not set.");
    public static string RssUrl =>
        Environment.GetEnvironmentVariable("RSS_URL") ?? throw new InvalidOperationException("RSS_URL is not set.");
 
} 