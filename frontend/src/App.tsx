import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Channels from './pages/Channels';
import ChannelDetail from './pages/ChannelDetail';
import Trending from './pages/Trending';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Channels />} />
          <Route path="channels/:id" element={<ChannelDetail />} />
          <Route path="trending" element={<Trending />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
