const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const webpack = require('webpack');

module.exports = (env, argv) => {
  const isProduction = argv.mode === 'production';
  
  return {
    mode: isProduction ? 'production' : 'development',
    entry: './src/index.js',
    output: {
      path: path.resolve(__dirname, 'dist'),
      filename: isProduction ? 'bundle.[contenthash].js' : 'bundle.js',
      clean: true,
      publicPath: '/',
    },
    module: {
      rules: [
        {
          test: /\.(js|jsx)$/,
          exclude: /node_modules/,
          use: {
            loader: 'babel-loader',
            options: {
              presets: ['@babel/preset-env', '@babel/preset-react']
            }
          }
        },
        {
          test: /\.css$/,
          use: ['style-loader', 'css-loader']
        },
        {
          test: /\.(png|svg|jpg|jpeg|gif)$/,
          type: 'asset/resource'
        }
      ]
    },
    plugins: [
      new HtmlWebpackPlugin({
        template: './public/index-react.html',
        filename: 'index.html',
        favicon: './public/images/logo.png'
      }),
      new CopyWebpackPlugin({
        patterns: [
          {
            from: 'public',
            to: '',
            globOptions: {
              ignore: ['**/index-react.html', '**/index.html'],
            },
          },
        ],
      }),
      new webpack.DefinePlugin({
        'process.env': {
          REACT_APP_STRIPE_PUBLISHABLE_KEY: JSON.stringify(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY || ''),
          REACT_APP_API_URL: JSON.stringify(process.env.REACT_APP_API_URL || 'http://localhost:5001'),
          NODE_ENV: JSON.stringify(process.env.NODE_ENV || 'development')
        }
      })
    ],
    devServer: {
      static: {
        directory: path.join(__dirname, 'public'),
        publicPath: '/',
      },
      compress: true,
      port: 3000,
      hot: true,
      historyApiFallback: true,
      host: 'localhost',
      client: {
        webSocketURL: 'auto://0.0.0.0:0/ws',
        overlay: true,
        progress: true,
      },
      webSocketServer: 'ws',
      allowedHosts: 'all',
      headers: {
        'Access-Control-Allow-Origin': '*',
      },
    },
    resolve: {
      extensions: ['.js', '.jsx']
    },
    devtool: isProduction ? 'source-map' : 'eval-source-map'
  };
}; 