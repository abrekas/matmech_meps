using Microsoft.Extensions.FileProviders;

var infrastructurePath = Path.GetFullPath(
    Path.Combine(Directory.GetCurrentDirectory(), "Infrastructure"));

var wwwrootPath = Path.Combine(infrastructurePath, "wwwroot");

var builder = WebApplication.CreateBuilder(new WebApplicationOptions
{
    WebRootPath = wwwrootPath,
    Args = args
});
builder.Services.AddControllers();
var app = builder.Build();
app.UseStaticFiles();
app.UseRouting();
app.MapControllers();
app.MapFallbackToFile("index.html");

app.Run();