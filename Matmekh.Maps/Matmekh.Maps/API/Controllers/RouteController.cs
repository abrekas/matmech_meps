using Matmekh.Maps.Models;
using Microsoft.AspNetCore.Mvc;
using Matmekh.Maps.Domain;

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

            PathFinder.FindPath(request.From, request.To);

            // Возвращаем результат
            return Ok(new
            {
                success = true,
                message = $"Маршрут от '{request.From}' до чиназес '{request.To}' построен!",
                from = request.From,
                to = request.To,
                distance = "700 км",
                duration = "8 часов"
            });
        }
    }
}
