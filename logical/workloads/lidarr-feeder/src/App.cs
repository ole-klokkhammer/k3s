using System;
using System.Net.Http;
using System.ServiceModel.Syndication;
using System.Threading;
using System.Threading.Tasks;
using System.Xml;
using System.Text.Json;
using System.Net;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Hosting;

public class App
{
    private readonly HttpClient http;
    private readonly CancellationToken appCt;
    private ILogger<App> logger;
    private const int LidarrQualityProfile = 3;
    private const int LidarrMetadataProfile = 2;
    private const string LidarrRootFolder = "/music";
    private const string UserAgent = "LidarrFeeder/1.0 (contact:ole.klokkhammer@outlook.com)";

    public App(ILogger<App> logger, HttpClient http, IHostApplicationLifetime lifetime)
    {
        this.logger = logger;
        this.http = http;
        this.appCt = lifetime.ApplicationStopping;
    }

    public async Task<int> RunOnceAsync()
    {
        using var reader = XmlReader.Create(AppEnvironment.RssUrl);
        var feed = SyndicationFeed.Load(reader);

        foreach (var item in feed.Items)
        {
            appCt.ThrowIfCancellationRequested();
            try
            {
                await OnRssItemAsync(item);
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "Error processing RSS item: {Title}", item.Title.Text);
            }
        }

        return 0;
    }

    public async Task OnRssItemAsync(SyndicationItem item)
    {
        string? artist = item.Categories != null && item.Categories.Count > 0
                         ? item.Categories[0].Name
                         : null;
        string? album = item.Summary?.Text;

        if (string.IsNullOrEmpty(artist) || string.IsNullOrEmpty(album))
        {
            logger.LogWarning("Skipping item with missing artist or album info.");
            return;
        }

        logger.LogInformation("Found: {Album} by {Artist}", album, artist);
        await OnAlbumFoundAsync(artist, album);
    }

    private async Task OnAlbumFoundAsync(string artist, string album)
    {
        logger.LogDebug("Waiting for 1 second to respect MusicBrainz rate limit");
        await Task.Delay(TimeSpan.FromSeconds(1), appCt);

        logger.LogDebug("Looking up MusicBrainz ID for artist: {Artist}", artist);
        string? artistMbid = await LookupMusicBrainzArtist(artist);
        if (string.IsNullOrEmpty(artistMbid))
        {
            logger.LogWarning("Could not find MusicBrainz ID for artist: {Artist}", artist);
            return;
        }

        bool artistExistsInLidarr = await ArtistExistsInLidarrByMbid(artistMbid);
        if (!artistExistsInLidarr)
        {
            logger.LogInformation("Adding artist with MBID: {MBID}", artistMbid);
            await AddArtistToLidarr(artist, artistMbid);
        }
        else
        {
            logger.LogInformation("Artist with MBID {MBID} already exists in Lidarr", artistMbid);
        }

        string? releaseMbid = await LookupMusicBrainzRelease(artistMbid, album);
        if (string.IsNullOrEmpty(releaseMbid))
        {
            logger.LogWarning("Could not find a MusicBrainz release for album '{Album}' by {Artist}", album, artist);
            return;
        }
        logger.LogInformation("Found release MBID {Release} for album '{Album}', adding album", releaseMbid, album);

        bool albumExistsInLidarr = await AlbumExistsInLidarrByMbid(releaseMbid);
        if (!albumExistsInLidarr)
        {
            logger.LogInformation("Adding album with MBID: {MBID}", releaseMbid);
            await AddAlbumToLidarr(artistMbid, releaseMbid);
        }
        else
        {
            logger.LogInformation("Album with MBID {MBID} already exists in Lidarr", releaseMbid);
        }

        logger.LogInformation("Done processing album '{Album}' by {Artist}", album, artist);
    }

    async Task<string?> LookupMusicBrainzArtist(string artist)
    {
        try
        {
            string url = $"https://musicbrainz.org/ws/2/artist/?query={Uri.EscapeDataString(artist)}&fmt=json";
            using var req = new HttpRequestMessage(HttpMethod.Get, url);
            req.Headers.UserAgent.ParseAdd(UserAgent);

            var resp = await http.SendAsync(req, appCt);
            if (resp.StatusCode == HttpStatusCode.Forbidden)
            {
                logger.LogWarning("MusicBrainz returned 403. Check User-Agent and rate limits.");
                return null;
            }
            resp.EnsureSuccessStatusCode();

            var respText = await resp.Content.ReadAsStringAsync(appCt);
            using var doc = JsonDocument.Parse(respText);
            if (doc.RootElement.TryGetProperty("artists", out var artists) && artists.GetArrayLength() > 0)
            {
                return artists[0].GetProperty("id").GetString();
            }
        }
        catch (OperationCanceledException) { throw; }
        catch (HttpRequestException ex)
        {
            logger.LogError(ex, "MusicBrainz lookup failed");
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Unexpected error during MusicBrainz artist lookup");
        }
        return null;
    }

    async Task<string?> LookupMusicBrainzRelease(string artistMbid, string albumTitle)
    {
        await Task.Delay(1100, appCt);

        string query = $"release:\"{albumTitle}\" AND arid:{artistMbid}";
        string url = $"https://musicbrainz.org/ws/2/release?query={Uri.EscapeDataString(query)}&fmt=json";

        try
        {
            using var req = new HttpRequestMessage(HttpMethod.Get, url);
            req.Headers.UserAgent.ParseAdd(UserAgent);

            var resp = await http.SendAsync(req, appCt);
            resp.EnsureSuccessStatusCode();

            var respText = await resp.Content.ReadAsStringAsync(appCt);
            using var doc = JsonDocument.Parse(respText);
            if (doc.RootElement.TryGetProperty("releases", out var releases) && releases.GetArrayLength() > 0)
            {
                var release = releases[0];
                if (release.TryGetProperty("release-group", out var rg) && rg.TryGetProperty("id", out var rgid))
                    return rgid.GetString(); // return release-group id (album MBID)
                return release.GetProperty("id").GetString(); // fallback to release id
            }
        }
        catch (OperationCanceledException) { throw; }
        catch (Exception ex)
        {
            logger.LogError(ex, "MusicBrainz release lookup failed");
        }
        return null;
    }

    async Task AddArtistToLidarr(string artist, string mbid)
    {
        var payload = new
        {
            artistName = artist,
            foreignArtistId = mbid,
            metadataProfileId = LidarrMetadataProfile,
            qualityProfileId = LidarrQualityProfile,
            rootFolderPath = LidarrRootFolder,
            monitored = true,
            addOptions = new { monitor = "all" }
        };

        var content = new StringContent(
            JsonSerializer.Serialize(payload),
            System.Text.Encoding.UTF8,
            "application/json"
        );

        string url = $"{AppEnvironment.LidarrUrl}/api/v1/artist?apikey={AppEnvironment.LidarrApiKey}";

        try
        {
            var resp = await http.PostAsync(url, content, appCt);
            resp.EnsureSuccessStatusCode();
            logger.LogInformation("Lidarr response: {StatusCode}", resp.StatusCode);
        }
        catch (OperationCanceledException) { throw; }
        catch (HttpRequestException ex)
        {
            logger.LogError(ex, "Lidarr request failed when adding artist");
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Unexpected error when adding artist to Lidarr");
        }
    }

    async Task AddAlbumToLidarr(string foreignArtistId, string foreignAlbumId)
    {
        var payload = new
        {
            artist = new
            {
                foreignArtistId,
                metadataProfileId = LidarrMetadataProfile,
                qualityProfileId = LidarrQualityProfile,
                rootFolderPath = LidarrRootFolder,
            },
            foreignAlbumId,
            monitored = true,
            addOptions = new { monitor = "all" }
        };

        var content = new StringContent(JsonSerializer.Serialize(payload),
                                        System.Text.Encoding.UTF8,
                                        "application/json");

        try
        {
            string url = $"{AppEnvironment.LidarrUrl}/api/v1/album?apikey={AppEnvironment.LidarrApiKey}";
            logger.LogInformation("Posting album to Lidarr");
            logger.LogDebug("Album payload: {Payload}", JsonSerializer.Serialize(payload));

            var resp = await http.PostAsync(url, content, appCt);
            logger.LogInformation("Lidarr album response: {StatusCode}", resp.StatusCode);
            if (!resp.IsSuccessStatusCode)
            {
                var respBody = await resp.Content.ReadAsStringAsync(appCt);
                logger.LogError("Lidarr returned {StatusCode} for {Url}. RequestPayload: {ReqPayload}.  ResponsePayload: {Payload}.",
                    resp.StatusCode,
                    url.ReplaceApiKey(),
                    payload,
                    respBody
                );
                return;
            }
        }
        catch (OperationCanceledException) { throw; }
        catch (Exception ex)
        {
            logger.LogError(ex, "Unexpected error when adding album to Lidarr");
        }
    }

    async Task<bool> ArtistExistsInLidarrByMbid(string mbid)
    {
        try
        {
            string url = $"{AppEnvironment.LidarrUrl}/api/v1/artist?apikey={AppEnvironment.LidarrApiKey}";
            var resp = await http.GetAsync(url, appCt);
            resp.EnsureSuccessStatusCode();

            var text = await resp.Content.ReadAsStringAsync(appCt);
            using var doc = JsonDocument.Parse(text);

            if (doc.RootElement.ValueKind == JsonValueKind.Array)
            {
                foreach (var el in doc.RootElement.EnumerateArray())
                {
                    if (el.TryGetProperty("foreignArtistId", out var fid) && fid.GetString() == mbid)
                    {
                        return true;
                    }
                }
            }
        }
        catch (OperationCanceledException) { throw; }
        catch (Exception ex)
        {
            logger.LogWarning(ex, "Failed to query Lidarr when checking for existing artist");
        }

        return false;
    }

    async Task<bool> AlbumExistsInLidarrByMbid(string foreignAlbumMbid)
    {
        try
        {
            string url = $"{AppEnvironment.LidarrUrl}/api/v1/album?apikey={AppEnvironment.LidarrApiKey}";
            var resp = await http.GetAsync(url, appCt);
            resp.EnsureSuccessStatusCode();

            var text = await resp.Content.ReadAsStringAsync(appCt);
            using var doc = JsonDocument.Parse(text);

            if (doc.RootElement.ValueKind == JsonValueKind.Array)
            {
                foreach (var el in doc.RootElement.EnumerateArray())
                {
                    // primary property used when adding albums in your app
                    if (el.TryGetProperty("foreignAlbumId", out var fa) && fa.GetString() == foreignAlbumMbid)
                        return true;

                    // some Lidarr responses may include other foreign id keys (fallbacks)
                    if (el.TryGetProperty("foreignReleaseId", out var fr) && fr.GetString() == foreignAlbumMbid)
                        return true;

                    if (el.TryGetProperty("releaseGroupId", out var rg) && rg.GetString() == foreignAlbumMbid)
                        return true;
                }
            }
        }
        catch (OperationCanceledException) { throw; }
        catch (Exception ex)
        {
            logger.LogWarning(ex, "Failed to query Lidarr when checking for existing album");
        }

        return false;
    }
}