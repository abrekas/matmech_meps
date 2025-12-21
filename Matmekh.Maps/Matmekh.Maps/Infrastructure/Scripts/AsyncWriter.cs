using System.Text;

namespace Matmekh.Maps.Infrastructure.Scripts
{
	public class AsyncWriter
	{
		private static readonly SemaphoreSlim _semaphore = new SemaphoreSlim(1, 1);

		public static async Task WriteToFileAsync(string content, string filePath)
		{
			Console.WriteLine(content);
			await _semaphore.WaitAsync();

			try
			{
				var directory = Path.GetDirectoryName(filePath);
				if (!string.IsNullOrEmpty(directory))
					Directory.CreateDirectory(directory);

				await using (var stream = new FileStream(
					filePath,
					FileMode.Append,
					FileAccess.Write,
					FileShare.Read,
					bufferSize: 4096,
					useAsync: true))
				{
					var bytes = Encoding.UTF8.GetBytes(content + Environment.NewLine);
					await stream.WriteAsync(bytes);
				}
			}
			finally
			{
				_semaphore.Release();
			}
		}
	}
}