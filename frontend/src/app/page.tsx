/**
 * Homepage - Dashboard
 */
export default function Home() {
  return (
    <main className="min-h-screen p-8">
      <h1 className="text-4xl font-bold mb-8">YouTube Analytics Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-2">Total Channels</h2>
          <p className="text-3xl font-bold">0</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-2">Total Videos</h2>
          <p className="text-3xl font-bold">0</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-2">Active Alerts</h2>
          <p className="text-3xl font-bold">0</p>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-2xl font-semibold mb-4">Getting Started</h2>
        <ol className="list-decimal list-inside space-y-2">
          <li>Add YouTube channels to track</li>
          <li>Configure alert rules</li>
          <li>Monitor performance metrics</li>
          <li>Analyze trends and growth</li>
        </ol>
      </div>
    </main>
  );
}
