export default function WorkingIndicator() {
  return (
    <div class="flex justify-start mb-4">
      <div class="bg-slate-800 border border-cyan-700 rounded-lg p-3 max-w-[80%]">
        <div class="flex items-center gap-3">
          <span class="w-4 h-4 border-2 border-cyan-300 border-t-transparent rounded-full animate-spin" />
          <span class="text-sm text-cyan-200">Working...</span>
        </div>
      </div>
    </div>
  );
}
