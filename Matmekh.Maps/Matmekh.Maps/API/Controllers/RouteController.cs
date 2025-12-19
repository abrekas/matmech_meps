using Microsoft.AspNetCore.Mvc;
using Matmekh.Maps.Infrastructure;
using System.Text.Json;
using Matmekh.Maps.Infrastructure.Models;
using Matmekh.Maps.Application;
using Matmekh.Maps.Domain.FindPath;
using Matmekh.Maps.Domain.ValueTypes;

namespace Matmekh.Maps.API.Controllers
{
    [ApiController]
    [Route("api/[controller]")]  // Будет: /api/route
    public class RouteController : ControllerBase
    {
        private readonly IPathFinderApp pathFinder;

        public RouteController(IPathFinderApp pathFinder) 
        { 
            this.pathFinder = pathFinder;
        }

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

            var graph = new List<Coordinates>();

            try
            {
                graph = pathFinder.FindPath(request.From, request.To).Points;
            }
            catch (Exception ex)
            {
				return BadRequest(new { error = ex.ToString() });
			}

            var options = new JsonSerializerOptions
            {
                WriteIndented = true,
                Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
            };

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
