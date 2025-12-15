using Microsoft.AspNetCore.Mvc;
using Matmekh.Maps.Infrastructure;
using System.Text.Json;
using Matmekh.Maps.Infrastructure.Models;
using Matmekh.Maps.Application;

namespace Matmekh.Maps.API.Controllers
{
    [ApiController]
    [Route("api/[controller]")]  // Будет: /api/route
    public class RouteController : ControllerBase
    {
        [HttpPost("build")]  // POST /api/route/build
        public IActionResult BuildRoute([FromBody] RouteRequest request)
        {
            // Проверка данных
            if (string.IsNullOrEmpty(request.From) || string.IsNullOrEmpty(request.To))
            {
                return BadRequest(new { error = "Заполните оба поля" });
            }

            // Здесь будет логика построения маршрута
            Console.WriteLine($"Построение маршрута: {request.From} → {request.To}");

            var graph = PathFinder.FindPath(request.From, request.To);

            var options = new JsonSerializerOptions
            {
                WriteIndented = true,
                Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
            };

            string json = JsonSerializer.Serialize(graph, options);

            string filePath = Path.Combine("Infrastructure", "result.json");
            Directory.CreateDirectory(Path.GetDirectoryName(filePath)!);
            System.IO.File.WriteAllText(filePath, json);

            return Ok(new
            {
                success = true,
                message = $"Маршрут от '{request.From}' до '{request.To}' построен!",
                from = request.From,
                to = request.To,
                path = graph
            });
        }
    }
}
