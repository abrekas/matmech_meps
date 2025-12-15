using Matmekh.Maps.Application;
using Matmekh.Maps.Domain.FindPath;

var builder = WebApplication.CreateBuilder(new WebApplicationOptions
{
    WebRootPath = Path.Combine("Infrastructure", "wwwroot"),
    Args = args
});

builder.Services.AddControllers();
builder.Services.AddScoped<ISearcher, AStar>();
builder.Services.AddScoped<IPathFinder, PathFinder>();

var app = builder.Build();

app.UseStaticFiles();
app.UseRouting();
app.MapControllers();
app.MapFallbackToFile("index.html");

app.Run();