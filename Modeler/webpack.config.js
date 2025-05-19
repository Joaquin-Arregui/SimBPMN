const path = require('path');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const { DefinePlugin } = require('webpack');

module.exports = (env, argv) => {
  const mode = argv.mode || 'development';
  const isDevMode = mode === 'development';

  return {
    mode,
    entry: {
      viewer: './example/src/viewer.js',
      modeler: './example/src/modeler.js'
    },
    output: {
      filename: 'dist/[name].js',
      path: path.resolve(__dirname, 'example'),
      clean: true
    },
    module: {
      rules: [
        {
          test: /\.bpmn$/,
          type: 'asset/source'
        },
        {
          test: /\.js$/,
          exclude: /node_modules/,
          use: {
            loader: 'babel-loader',
            options: {
              presets: ['@babel/preset-env']
            }
          }
        },
        {
          test: /\.json$/,
          type: 'json',
          parser: {
            parse: JSON.parse
          }
        },
        {
          test: /\.css$/,
          use: ['style-loader', 'css-loader']
        },
        {
          test: /\.less$/,
          use: ['style-loader', 'css-loader', 'less-loader']
        },
        {
          test: /\.svg$/,
          use: 'raw-loader'
        }
      ]
    },
    resolve: {
      fallback: {
        fs: false,
        path: require.resolve('path-browserify'),
        crypto: require.resolve('crypto-browserify'),
        stream: require.resolve('stream-browserify'),
        buffer: require.resolve('buffer/')
      }
    },
    plugins: [
      new CopyWebpackPlugin({
        patterns: [
          { from: 'bpmn-js/dist/assets', context: 'node_modules', to: 'dist/vendor/bpmn-js/assets' },
          { from: '@bpmn-io/properties-panel/dist/assets', context: 'node_modules', to: 'dist/vendor/bpmn-js-properties-panel/assets' }
        ]
      }),
    ],
    devtool: isDevMode ? 'eval-source-map' : 'source-map',
    devServer: {
      static: path.join(__dirname, 'example'),
      compress: true,
      port: 9000,
      hot: true,
      open: true,
      liveReload: false
    }
  };
};
