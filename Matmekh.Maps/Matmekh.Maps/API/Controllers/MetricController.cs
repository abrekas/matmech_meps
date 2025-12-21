using Microsoft.AspNetCore.Mvc;
using Matmekh.Maps.Infrastructure.Scripts;

namespace Matmekh.Maps.API.Controllers
{
	[ApiController]
	[Route("api/[controller]")]
	public class MetricController : ControllerBase
	{
		private static readonly object _fileLock = new object();
		private static readonly string _filePath = Path.Combine("Infrastructure", "metrics.txt");

		[HttpPost("build")]
		public async Task<IActionResult> BuildMetric([FromBody] MetricRequest request)
		{
			if (request == null)
				return BadRequest("Invalid request");

			try
			{
				
				var logEntry = ";" + request.startedAt + " " + request.activeMs.ToString();
				
				await AsyncWriter.WriteToFileAsync(logEntry, _filePath);

				return Ok();
			}
			catch (Exception ex)
			{
				return StatusCode(500, "Internal server error");
			}
		}

		public class MetricRequest
		{
			public string? startedAt { get; set; }
			public long activeMs { get; set; }
			public string? page { get; set; }
		}
	}
}