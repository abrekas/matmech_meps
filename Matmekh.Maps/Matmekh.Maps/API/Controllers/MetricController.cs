using Microsoft.AspNetCore.Mvc;
using System.Text;
using static System.Net.Mime.MediaTypeNames;

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

				await WriteToFileAsync(logEntry);

				return Ok();
			}
			catch (Exception ex)
			{
				return StatusCode(500, "Internal server error");
			}
		}

		private static async Task WriteToFileAsync(string content)
		{
			var directory = Path.GetDirectoryName(_filePath);
			if (!string.IsNullOrEmpty(directory))
				Directory.CreateDirectory(directory);

			await using (var stream = new FileStream(
				_filePath,
				FileMode.Append,
				FileAccess.Write,
				FileShare.Read,
				bufferSize: 4096,
				useAsync: true))
			{
				var bytes = Encoding.UTF8.GetBytes(content);
				await stream.WriteAsync(bytes);
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