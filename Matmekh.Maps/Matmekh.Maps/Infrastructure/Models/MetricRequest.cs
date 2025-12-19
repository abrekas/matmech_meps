namespace Matmekh.Maps.Infrastructure.Models
{
    public class MetricRequest
    {
		public string name { get; set; } = string.Empty;
		public int activeMs { get; set; }
		public string startedAt { get; set; } = string.Empty;
		public string finishedAt { get; set; } = string.Empty;
		public string reason { get; set; } = string.Empty;
	}
}
