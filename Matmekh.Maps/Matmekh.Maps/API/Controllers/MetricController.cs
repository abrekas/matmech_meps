using Microsoft.AspNetCore.Mvc;
using Matmekh.Maps.Infrastructure;
using System.Text.Json;
using Matmekh.Maps.Infrastructure.Models;
using Matmekh.Maps.Application;
using Matmekh.Maps.Domain.FindPath;
using Matmekh.Maps.Domain.ValueTypes;
using Microsoft.Extensions.Options;

namespace Matmekh.Maps.API.Controllers
{
	[ApiController]
	[Route("api/[controller]")]
	public class MetricController : ControllerBase
	{
		[HttpPost("build")]  // POST /api/metric/build
		public void BuildMetric([FromBody] MetricRequest request)
		{

			string filePath = Path.Combine("Infrastructure", "metric.txt");
			var text = System.IO.File.ReadAllText(filePath);
			var newText = text + ";" + request.startedAt + " " + request.activeMs.ToString();
			Directory.CreateDirectory(Path.GetDirectoryName(filePath)!);
			System.IO.File.WriteAllText(filePath, newText);
		}
	}
}
