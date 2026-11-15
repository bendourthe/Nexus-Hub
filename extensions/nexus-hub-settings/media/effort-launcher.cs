using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading.Tasks;
using System.Web.Script.Serialization;

// Starts the bundled editor runtime as Node and relays inherited protocol streams.
// No shell, terminal window, permissions switch, or credential handling is involved.
internal static class EffortLauncher
{
    [StructLayout(LayoutKind.Sequential)]
    private struct ProcessBasicInformation
    {
        public IntPtr ExitStatus, PebAddress, AffinityMask, BasePriority, ProcessId, ParentProcessId;
    }
    [DllImport("ntdll.dll")]
    private static extern int NtQueryInformationProcess(IntPtr process, int kind, ref ProcessBasicInformation information, int size, out int returned);

    private static long ParentId(Process process)
    {
        var information = new ProcessBasicInformation();
        int returned;
        return NtQueryInformationProcess(process.Handle, 0, ref information, Marshal.SizeOf(information), out returned) == 0 ? information.ParentProcessId.ToInt64() : 0;
    }

    private static string Quote(string value)
    {
        var result = new StringBuilder("\"");
        int slashes = 0;
        foreach (char item in value)
        {
            if (item == '\\') { slashes++; continue; }
            result.Append('\\', item == '"' ? slashes * 2 + 1 : slashes);
            result.Append(item);
            slashes = 0;
        }
        result.Append('\\', slashes * 2);
        return result.Append('"').ToString();
    }

    private static int Main(string[] args)
    {
        if (args.Length == 2 && args[0] == "--nexus-editor-connections") {
            int editor;
            if (!Int32.TryParse(args[1], out editor) || editor <= 0) return 1;
            var providers = new List<string>();
            foreach (var name in new[] { "claude", "codex" }) {
                foreach (var process in Process.GetProcessesByName(name)) {
                    using (process) { try { if (ParentId(process) == editor && !providers.Contains(name)) providers.Add(name); } catch { } }
                }
            }
            Console.Write(new JavaScriptSerializer().Serialize(providers));
            return 0;
        }
        Process child = null;
        try
        {
            string configuration = Path.ChangeExtension(Assembly.GetEntryAssembly().Location, ".json");
            var values = new JavaScriptSerializer().Deserialize<Dictionary<string, object>>(File.ReadAllText(configuration));
            var start = new ProcessStartInfo((string)values["runtime"]);
            start.Arguments = String.Join(" ", new[] { (string)values["script"], configuration }.Concat(args).Select(Quote));
            start.UseShellExecute = false;
            start.CreateNoWindow = true;
            start.WindowStyle = ProcessWindowStyle.Hidden;
            start.RedirectStandardInput = true;
            start.RedirectStandardOutput = true;
            start.RedirectStandardError = true;
            start.EnvironmentVariables["ELECTRON_RUN_AS_NODE"] = "1";
            start.EnvironmentVariables["NEXUS_EFFORT_CLIENT_PID"] = ParentId(Process.GetCurrentProcess()).ToString();
            child = Process.Start(start);
            var input = child.StandardInput.BaseStream;
            Task.Run(async () => {
                try {
                    var source = Console.OpenStandardInput();
                    var buffer = new byte[4096];
                    int count;
                    while ((count = await source.ReadAsync(buffer, 0, buffer.Length)) > 0) {
                        await input.WriteAsync(buffer, 0, count);
                        await input.FlushAsync();
                    }
                } catch (IOException) { } finally { input.Close(); }
            });
            Task.WaitAll(child.StandardOutput.BaseStream.CopyToAsync(Console.OpenStandardOutput()), child.StandardError.BaseStream.CopyToAsync(Console.OpenStandardError()));
            child.WaitForExit();
            return child.ExitCode;
        }
        catch
        {
            if (child != null) { try { if (!child.HasExited) child.Kill(); } catch { } }
            Console.Error.WriteLine("Nexus live effort: the local protocol launcher could not start.");
            return 1;
        }
    }
}
