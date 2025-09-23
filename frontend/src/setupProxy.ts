import { Express } from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';

module.exports = function(app: Express) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'https://pfs-be-01-buf0fwgnfgbechdu.centralus-01.azurewebsites.net',
      changeOrigin: true,
      cookieDomainRewrite: 'localhost',
      onProxyReq: (proxyReq, req, res) => {
        proxyReq.setHeader('Origin', 'http://localhost:3000');
      },
    })
  );
};
