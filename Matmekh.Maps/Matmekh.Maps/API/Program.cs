var builder = WebApplication.CreateBuilder(new WebApplicationOptions
{
    WebRootPath = Path.Combine("Infrastructure", "wwwroot"),
    Args = args
});

builder.Services.AddControllers();

var app = builder.Build();

app.UseStaticFiles();
app.UseRouting();
app.MapControllers();
app.MapFallbackToFile("index.html");

app.Run();