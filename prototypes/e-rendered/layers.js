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
   "x": 455.97,
   "y": 543.78,
   "w": 114.83,
   "h": 109.33
  },
  "honey": {
   "src": "img/touch-honey.webp",
   "x": 608.35,
   "y": 546.46,
   "w": 63.5,
   "h": 108.75
  },
  "dice": {
   "src": "img/touch-dice.webp",
   "x": 921.19,
   "y": 623.28,
   "w": 33.8,
   "h": 32.2
  },
  "panther": {
   "src": "img/touch-panther.webp",
   "x": 961.57,
   "y": 503.37,
   "w": 306.0,
   "h": 147.0
  }
 },
 "bottles": {
  "bourbon": {
   "src": "img/bottle-bourbon.webp",
   "x": 773.76,
   "y": 279.55,
   "w": 53.08,
   "h": 106.54,
   "ax": 800,
   "ay": 384,
   "family": "whisky"
  },
  "rye": {
   "src": "img/bottle-rye.webp",
   "x": 773.76,
   "y": 279.55,
   "w": 53.08,
   "h": 106.54,
   "ax": 800,
   "ay": 384,
   "family": "whisky"
  },
  "blended scotch": {
   "src": "img/bottle-blended-scotch.webp",
   "x": 773.76,
   "y": 279.55,
   "w": 53.08,
   "h": 106.54,
   "ax": 800,
   "ay": 384,
   "family": "whisky"
  },
  "islay scotch": {
   "src": "img/bottle-islay-scotch.webp",
   "x": 773.76,
   "y": 279.55,
   "w": 53.08,
   "h": 106.54,
   "ax": 800,
   "ay": 384,
   "family": "whisky"
  },
  "irish whiskey": {
   "src": "img/bottle-irish-whiskey.webp",
   "x": 773.76,
   "y": 279.55,
   "w": 53.08,
   "h": 106.54,
   "ax": 800,
   "ay": 384,
   "family": "whisky"
  },
  "london dry gin": {
   "src": "img/bottle-london-dry-gin.webp",
   "x": 783.95,
   "y": 279.56,
   "w": 32.31,
   "h": 106.15,
   "ax": 800,
   "ay": 384,
   "family": "gin"
  },
  "white rum": {
   "src": "img/bottle-white-rum.webp",
   "x": 776.56,
   "y": 279.58,
   "w": 46.92,
   "h": 106.54,
   "ax": 800,
   "ay": 384,
   "family": "rum"
  },
  "tequila": {
   "src": "img/bottle-tequila.webp",
   "x": 780.79,
   "y": 279.58,
   "w": 38.46,
   "h": 106.54,
   "ax": 800,
   "ay": 384,
   "family": "tequila"
  },
  "vodka": {
   "src": "img/bottle-vodka.webp",
   "x": 786.05,
   "y": 279.59,
   "w": 28.46,
   "h": 106.15,
   "ax": 800,
   "ay": 384,
   "family": "vodka"
  },
  "cognac": {
   "src": "img/bottle-cognac.webp",
   "x": 772.73,
   "y": 279.58,
   "w": 54.62,
   "h": 105.38,
   "ax": 800,
   "ay": 384,
   "family": "brandy"
  },
  "sweet vermouth": {
   "src": "img/bottle-sweet-vermouth.webp",
   "x": 781.84,
   "y": 279.59,
   "w": 36.92,
   "h": 106.54,
   "ax": 800,
   "ay": 384,
   "family": "aperitif"
  },
  "dry vermouth": {
   "src": "img/bottle-dry-vermouth.webp",
   "x": 781.84,
   "y": 279.59,
   "w": 36.92,
   "h": 106.54,
   "ax": 800,
   "ay": 384,
   "family": "aperitif"
  },
  "campari": {
   "src": "img/bottle-campari.webp",
   "x": 781.84,
   "y": 279.59,
   "w": 36.92,
   "h": 106.54,
   "ax": 800,
   "ay": 384,
   "family": "aperitif"
  },
  "aperol": {
   "src": "img/bottle-aperol.webp",
   "x": 781.84,
   "y": 279.59,
   "w": 36.92,
   "h": 106.54,
   "ax": 800,
   "ay": 384,
   "family": "aperitif"
  },
  "amaro nonino": {
   "src": "img/bottle-amaro-nonino.webp",
   "x": 781.84,
   "y": 279.59,
   "w": 36.92,
   "h": 106.54,
   "ax": 800,
   "ay": 384,
   "family": "aperitif"
  },
  "triple sec": {
   "src": "img/bottle-triple-sec.webp",
   "x": 786.05,
   "y": 279.59,
   "w": 28.46,
   "h": 106.15,
   "ax": 800,
   "ay": 384,
   "family": "vodka"
  },
  "amaretto": {
   "src": "img/bottle-amaretto.webp",
   "x": 772.73,
   "y": 279.58,
   "w": 54.62,
   "h": 105.38,
   "ax": 800,
   "ay": 384,
   "family": "brandy"
  },
  "cherry heering": {
   "src": "img/bottle-cherry-heering.webp",
   "x": 772.73,
   "y": 279.58,
   "w": 54.62,
   "h": 105.38,
   "ax": 800,
   "ay": 384,
   "family": "brandy"
  },
  "ginger wine": {
   "src": "img/bottle-ginger-wine.webp",
   "x": 781.84,
   "y": 279.59,
   "w": 36.92,
   "h": 106.54,
   "ax": 800,
   "ay": 384,
   "family": "aperitif"
  },
  "coffee liqueur": {
   "src": "img/bottle-coffee-liqueur.webp",
   "x": 776.56,
   "y": 279.58,
   "w": 46.92,
   "h": 106.54,
   "ax": 800,
   "ay": 384,
   "family": "rum"
  },
  "angostura bitters": {
   "src": "img/bottle-angostura-bitters.webp",
   "x": 786.05,
   "y": 315.84,
   "w": 28.46,
   "h": 68.85,
   "ax": 800,
   "ay": 384,
   "family": "bitters"
  },
  "orange bitters": {
   "src": "img/bottle-orange-bitters.webp",
   "x": 786.05,
   "y": 315.84,
   "w": 28.46,
   "h": 68.85,
   "ax": 800,
   "ay": 384,
   "family": "bitters"
  },
  "ginger ale": {
   "src": "img/bottle-ginger-ale.webp",
   "x": 785.93,
   "y": 304.17,
   "w": 28.46,
   "h": 81.54,
   "ax": 800,
   "ay": 384,
   "family": "mixer"
  },
  "ginger beer": {
   "src": "img/bottle-ginger-beer.webp",
   "x": 785.93,
   "y": 304.17,
   "w": 28.46,
   "h": 81.54,
   "ax": 800,
   "ay": 384,
   "family": "mixer"
  },
  "soda water": {
   "src": "img/bottle-soda-water.webp",
   "x": 785.93,
   "y": 304.17,
   "w": 28.46,
   "h": 81.54,
   "ax": 800,
   "ay": 384,
   "family": "mixer"
  },
  "tonic water": {
   "src": "img/bottle-tonic-water.webp",
   "x": 785.93,
   "y": 304.17,
   "w": 28.46,
   "h": 81.54,
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
const RENDER_LOG = [{"layer": "b_bourbon", "px": [164, 303], "samples": 32, "seconds": 0.8}, {"layer": "b_rye", "px": [164, 303], "samples": 32, "seconds": 0.7}, {"layer": "b_blended_scotch", "px": [164, 303], "samples": 32, "seconds": 0.7}, {"layer": "b_islay_scotch", "px": [164, 303], "samples": 32, "seconds": 0.7}, {"layer": "b_irish_whiskey", "px": [164, 303], "samples": 32, "seconds": 0.7}, {"layer": "b_london_dry_gin", "px": [109, 301], "samples": 32, "seconds": 0.5}, {"layer": "b_white_rum", "px": [148, 302], "samples": 32, "seconds": 0.6}, {"layer": "b_tequila", "px": [126, 302], "samples": 32, "seconds": 0.6}, {"layer": "b_vodka", "px": [99, 301], "samples": 32, "seconds": 0.4}, {"layer": "b_cognac", "px": [168, 303], "samples": 32, "seconds": 0.6}, {"layer": "b_sweet_vermouth", "px": [120, 301], "samples": 32, "seconds": 0.5}, {"layer": "b_dry_vermouth", "px": [120, 301], "samples": 32, "seconds": 0.5}, {"layer": "b_campari", "px": [120, 301], "samples": 32, "seconds": 0.5}, {"layer": "b_aperol", "px": [120, 301], "samples": 32, "seconds": 0.5}, {"layer": "b_amaro_nonino", "px": [120, 301], "samples": 32, "seconds": 0.5}, {"layer": "b_triple_sec", "px": [99, 301], "samples": 32, "seconds": 0.4}, {"layer": "b_amaretto", "px": [168, 303], "samples": 32, "seconds": 0.7}, {"layer": "b_cherry_heering", "px": [168, 303], "samples": 32, "seconds": 0.7}, {"layer": "b_ginger_wine", "px": [120, 301], "samples": 32, "seconds": 0.5}, {"layer": "b_coffee_liqueur", "px": [148, 302], "samples": 32, "seconds": 0.6}, {"layer": "b_angostura_bitters", "px": [101, 206], "samples": 32, "seconds": 0.3}, {"layer": "b_orange_bitters", "px": [101, 206], "samples": 32, "seconds": 0.3}, {"layer": "b_ginger_ale", "px": [99, 237], "samples": 32, "seconds": 0.4}, {"layer": "b_ginger_beer", "px": [99, 237], "samples": 32, "seconds": 0.4}, {"layer": "b_soda_water", "px": [99, 237], "samples": 32, "seconds": 0.4}, {"layer": "b_tonic_water", "px": [99, 237], "samples": 32, "seconds": 0.4}, {"layer": "panther_preview", "px": [1731, 911], "samples": 48, "seconds": 20.0}, {"layer": "t_menu", "px": [851, 835], "samples": 64, "seconds": 13.1}, {"layer": "t_honey", "px": [376, 547], "samples": 64, "seconds": 4.1}, {"layer": "t_dice", "px": [312, 302], "samples": 64, "seconds": 1.8}, {"layer": "t_panther", "px": [1039, 547], "samples": 64, "seconds": 9.7}, {"layer": "bg_bar", "px": [2000, 2000], "samples": 64, "seconds": 121.8}, {"layer": "bg_sign", "px": [1480, 460], "samples": 64, "seconds": 29.0}, {"layer": "bg_shelf", "px": [1672, 1065], "samples": 64, "seconds": 75.2}, {"layer": "bg_mid", "px": [2222, 1232], "samples": 64, "seconds": 104.6}, {"layer": "bg_menu", "px": [1380, 1080], "samples": 48, "seconds": 46.7}, {"layer": "bg_sign_off", "px": [1480, 460], "samples": 64, "seconds": 20.5}];
