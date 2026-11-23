/* Written by blender/build_bar.py: where each rendered layer sits, in world units (prototype B's SVG space). */
const LAYERS = {
 "bg": {
  "bar": {
   "src": "img/bg-bar.webp",
   "x": 0,
   "y": -240,
   "w": 1600,
   "h": 1600
  },
  "sign": {
   "src": "img/bg-sign.webp",
   "x": 430,
   "y": 20,
   "w": 740,
   "h": 230
  },
  "shelf": {
   "src": "img/bg-shelf.webp",
   "x": 420,
   "y": 96,
   "w": 760,
   "h": 484
  },
  "mid": {
   "src": "img/bg-mid.webp",
   "x": 280,
   "y": 250,
   "w": 1010,
   "h": 560
  },
  "menu": {
   "src": "img/bg-menu.webp",
   "x": 400,
   "y": 520,
   "w": 230,
   "h": 180
  },
  "signOff": {
   "src": "img/bg-sign-off.webp",
   "x": 430,
   "y": 20,
   "w": 740,
   "h": 230
  }
 },
 "touch": {
  "menu": {
   "src": "img/touch-menu.webp",
   "x": 459.61,
   "y": 538.38,
   "w": 109.0,
   "h": 112.0
  },
  "honey": {
   "src": "img/touch-honey.webp",
   "x": 608.76,
   "y": 543.03,
   "w": 62.5,
   "h": 112.0
  },
  "dice": {
   "src": "img/touch-dice.webp",
   "x": 918.91,
   "y": 623.72,
   "w": 38.4,
   "h": 32.6
  },
  "panther": {
   "src": "img/touch-panther.webp",
   "x": 950.36,
   "y": 432.21,
   "w": 230.33,
   "h": 226.67
  }
 },
 "bottles": {
  "bourbon": {
   "src": "img/bottle-bourbon.webp",
   "x": 771.29,
   "y": 283.75,
   "w": 57.69,
   "h": 102.69,
   "ax": 800,
   "ay": 384,
   "family": "whisky"
  },
  "rye": {
   "src": "img/bottle-rye.webp",
   "x": 775.5,
   "y": 282.94,
   "w": 49.23,
   "h": 103.08,
   "ax": 800,
   "ay": 384,
   "family": "whisky"
  },
  "blended scotch": {
   "src": "img/bottle-blended-scotch.webp",
   "x": 772.72,
   "y": 283.77,
   "w": 54.23,
   "h": 102.69,
   "ax": 800,
   "ay": 384,
   "family": "whisky"
  },
  "islay scotch": {
   "src": "img/bottle-islay-scotch.webp",
   "x": 775.98,
   "y": 283.75,
   "w": 48.46,
   "h": 102.31,
   "ax": 800,
   "ay": 384,
   "family": "whisky"
  },
  "irish whiskey": {
   "src": "img/bottle-irish-whiskey.webp",
   "x": 776.4,
   "y": 282.95,
   "w": 47.31,
   "h": 103.08,
   "ax": 800,
   "ay": 384,
   "family": "whisky"
  },
  "london dry gin": {
   "src": "img/bottle-london-dry-gin.webp",
   "x": 783.64,
   "y": 284.22,
   "w": 33.08,
   "h": 101.54,
   "ax": 800,
   "ay": 384,
   "family": "gin"
  },
  "white rum": {
   "src": "img/bottle-white-rum.webp",
   "x": 776.7,
   "y": 286.18,
   "w": 46.54,
   "h": 99.62,
   "ax": 800,
   "ay": 384,
   "family": "rum"
  },
  "tequila": {
   "src": "img/bottle-tequila.webp",
   "x": 780.72,
   "y": 282.47,
   "w": 39.23,
   "h": 103.46,
   "ax": 800,
   "ay": 384,
   "family": "tequila"
  },
  "vodka": {
   "src": "img/bottle-vodka.webp",
   "x": 786.38,
   "y": 285.27,
   "w": 27.69,
   "h": 100.38,
   "ax": 800,
   "ay": 384,
   "family": "vodka"
  },
  "cognac": {
   "src": "img/bottle-cognac.webp",
   "x": 773.01,
   "y": 285.04,
   "w": 54.62,
   "h": 100.38,
   "ax": 800,
   "ay": 384,
   "family": "brandy"
  },
  "sweet vermouth": {
   "src": "img/bottle-sweet-vermouth.webp",
   "x": 782.03,
   "y": 290.11,
   "w": 36.15,
   "h": 95.77,
   "ax": 800,
   "ay": 384,
   "family": "aperitif"
  },
  "dry vermouth": {
   "src": "img/bottle-dry-vermouth.webp",
   "x": 782.13,
   "y": 290.11,
   "w": 36.15,
   "h": 95.77,
   "ax": 800,
   "ay": 384,
   "family": "aperitif"
  },
  "campari": {
   "src": "img/bottle-campari.webp",
   "x": 782.03,
   "y": 290.11,
   "w": 36.15,
   "h": 95.77,
   "ax": 800,
   "ay": 384,
   "family": "aperitif"
  },
  "aperol": {
   "src": "img/bottle-aperol.webp",
   "x": 781.92,
   "y": 290.11,
   "w": 36.15,
   "h": 95.77,
   "ax": 800,
   "ay": 384,
   "family": "aperitif"
  },
  "amaro nonino": {
   "src": "img/bottle-amaro-nonino.webp",
   "x": 782.01,
   "y": 290.11,
   "w": 36.15,
   "h": 95.77,
   "ax": 800,
   "ay": 384,
   "family": "aperitif"
  },
  "triple sec": {
   "src": "img/bottle-triple-sec.webp",
   "x": 786.28,
   "y": 285.28,
   "w": 27.69,
   "h": 100.38,
   "ax": 800,
   "ay": 384,
   "family": "vodka"
  },
  "amaretto": {
   "src": "img/bottle-amaretto.webp",
   "x": 773.04,
   "y": 285.05,
   "w": 54.62,
   "h": 100.38,
   "ax": 800,
   "ay": 384,
   "family": "brandy"
  },
  "cherry heering": {
   "src": "img/bottle-cherry-heering.webp",
   "x": 772.85,
   "y": 285.04,
   "w": 54.62,
   "h": 100.38,
   "ax": 800,
   "ay": 384,
   "family": "brandy"
  },
  "ginger wine": {
   "src": "img/bottle-ginger-wine.webp",
   "x": 782.29,
   "y": 290.11,
   "w": 36.15,
   "h": 95.77,
   "ax": 800,
   "ay": 384,
   "family": "aperitif"
  },
  "coffee liqueur": {
   "src": "img/bottle-coffee-liqueur.webp",
   "x": 776.63,
   "y": 286.18,
   "w": 46.54,
   "h": 99.62,
   "ax": 800,
   "ay": 384,
   "family": "rum"
  },
  "angostura bitters": {
   "src": "img/bottle-angostura-bitters.webp",
   "x": 786.9,
   "y": 318.28,
   "w": 26.92,
   "h": 67.31,
   "ax": 800,
   "ay": 384,
   "family": "bitters"
  },
  "orange bitters": {
   "src": "img/bottle-orange-bitters.webp",
   "x": 786.7,
   "y": 318.28,
   "w": 26.92,
   "h": 67.31,
   "ax": 800,
   "ay": 384,
   "family": "bitters"
  },
  "ginger ale": {
   "src": "img/bottle-ginger-ale.webp",
   "x": 786.24,
   "y": 311.39,
   "w": 27.69,
   "h": 74.23,
   "ax": 800,
   "ay": 384,
   "family": "mixer"
  },
  "ginger beer": {
   "src": "img/bottle-ginger-beer.webp",
   "x": 786.18,
   "y": 311.4,
   "w": 27.69,
   "h": 74.23,
   "ax": 800,
   "ay": 384,
   "family": "mixer"
  },
  "soda water": {
   "src": "img/bottle-soda-water.webp",
   "x": 786.19,
   "y": 311.39,
   "w": 27.69,
   "h": 74.23,
   "ax": 800,
   "ay": 384,
   "family": "mixer"
  },
  "tonic water": {
   "src": "img/bottle-tonic-water.webp",
   "x": 786.17,
   "y": 311.4,
   "w": 27.69,
   "h": 74.23,
   "ax": 800,
   "ay": 384,
   "family": "mixer"
  }
 },
 "frame": [
  0,
  -240,
  1600,
  1360
 ],
 "counterBackY": 629.9,
 "counterFrontY": 658,
 "surface": {
  "-1.0": 652.9,
  "-0.85": 650.4,
  "-0.75": 648.7,
  "-0.55": 645.5
 },
 "settings": {
  "engine": "Cycles (CPU)",
  "denoiser": "OpenImageDenoise",
  "adaptiveThreshold": 0.02,
  "maxBounces": 4,
  "viewTransform": "Standard",
  "quick": false
 }
};
const RENDER_LOG = [{"layer": "panther_preview", "px": [1313, 1352], "samples": 48, "seconds": 33.8}, {"layer": "t_menu", "px": [816, 834], "samples": 64, "seconds": 54.9}, {"layer": "t_honey", "px": [371, 570], "samples": 64, "seconds": 29.6}, {"layer": "t_dice", "px": [426, 308], "samples": 64, "seconds": 10.7}, {"layer": "t_panther", "px": [788, 811], "samples": 64, "seconds": 33.0}, {"layer": "bg_bar", "px": [2000, 2000], "samples": 64, "seconds": 311.0}, {"layer": "bg_sign", "px": [1480, 460], "samples": 64, "seconds": 63.4}, {"layer": "bg_shelf", "px": [1672, 1065], "samples": 64, "seconds": 178.5}, {"layer": "bg_mid", "px": [2222, 1232], "samples": 64, "seconds": 243.6}, {"layer": "bg_menu", "px": [1380, 1080], "samples": 48, "seconds": 108.7}, {"layer": "bg_sign_off", "px": [1480, 460], "samples": 64, "seconds": 54.1}, {"layer": "b_bourbon", "px": [182, 292], "samples": 160, "seconds": 17.4}, {"layer": "b_rye", "px": [158, 294], "samples": 160, "seconds": 9.2}, {"layer": "b_blended_scotch", "px": [169, 292], "samples": 160, "seconds": 16.6}, {"layer": "b_islay_scotch", "px": [174, 292], "samples": 160, "seconds": 8.1}, {"layer": "b_irish_whiskey", "px": [156, 294], "samples": 160, "seconds": 11.4}, {"layer": "b_london_dry_gin", "px": [112, 289], "samples": 160, "seconds": 7.6}, {"layer": "b_white_rum", "px": [156, 285], "samples": 160, "seconds": 7.4}, {"layer": "b_tequila", "px": [129, 294], "samples": 160, "seconds": 10.1}, {"layer": "b_vodka", "px": [103, 286], "samples": 160, "seconds": 7.9}, {"layer": "b_cognac", "px": [176, 289], "samples": 160, "seconds": 7.1}, {"layer": "b_sweet_vermouth", "px": [123, 274], "samples": 160, "seconds": 8.9}, {"layer": "b_dry_vermouth", "px": [122, 274], "samples": 160, "seconds": 8.9}, {"layer": "b_campari", "px": [123, 274], "samples": 160, "seconds": 6.0}, {"layer": "b_aperol", "px": [125, 274], "samples": 160, "seconds": 6.0}, {"layer": "b_amaro_nonino", "px": [124, 274], "samples": 160, "seconds": 5.9}, {"layer": "b_triple_sec", "px": [100, 286], "samples": 160, "seconds": 5.3}, {"layer": "b_amaretto", "px": [170, 289], "samples": 160, "seconds": 14.7}, {"layer": "b_cherry_heering", "px": [178, 289], "samples": 160, "seconds": 6.4}, {"layer": "b_ginger_wine", "px": [122, 274], "samples": 160, "seconds": 5.7}, {"layer": "b_coffee_liqueur", "px": [154, 285], "samples": 160, "seconds": 13.0}, {"layer": "b_angostura_bitters", "px": [96, 201], "samples": 160, "seconds": 2.7}, {"layer": "b_orange_bitters", "px": [95, 201], "samples": 160, "seconds": 2.2}, {"layer": "b_ginger_ale", "px": [101, 218], "samples": 160, "seconds": 4.2}, {"layer": "b_ginger_beer", "px": [98, 218], "samples": 160, "seconds": 3.9}, {"layer": "b_soda_water", "px": [102, 218], "samples": 160, "seconds": 8.3}, {"layer": "b_tonic_water", "px": [100, 218], "samples": 160, "seconds": 8.2}];
