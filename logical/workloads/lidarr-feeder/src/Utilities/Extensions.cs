internal static class Extensions
{
    private static string RedactField(string url, string field)
    {
        try
        {
            var uri = new Uri(url);
            var qb = System.Web.HttpUtility.ParseQueryString(uri.Query);
            if (qb[field] != null) qb[field] = "***REDACTED***";
            var builder = new UriBuilder(uri) { Query = qb.ToString() ?? string.Empty };
            return builder.ToString();
        }
        catch
        {
            return url;
        }
    }
    public static string ReplaceApiKey(this string url)
    {
        return RedactField(url, "apikey");
    }
}