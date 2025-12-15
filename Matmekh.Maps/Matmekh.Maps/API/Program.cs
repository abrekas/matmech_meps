using Matmekh.Maps.Application;
using Matmekh.Maps.Domain.FindPath;
using Matmekh.Maps.Infrastructure.Scripts;

namespace Matmekh.Maps.API;

class Program
{
    static void Main(string[] args)
    {
        var builder = WebApplication.CreateBuilder(new WebApplicationOptions
        {
            WebRootPath = Path.Combine("Infrastructure", "wwwroot"),
            Args = args
        });

        builder.Services.AddControllers();

        builder.Services.AddScoped<ISearcher, AStar>();
        builder.Services.AddScoped<IPathFinderService, PathFinderService>();
        builder.Services.AddScoped<IJSONGraphLoader, JSONGraphLoader>();
        builder.Services.AddScoped<IPathFinderApp, PathFinderApp>();

        var app = builder.Build();

        app.UseStaticFiles();
        app.UseRouting();
        app.MapControllers();
        app.MapFallbackToFile("index.html");

        app.Run();
    }
}