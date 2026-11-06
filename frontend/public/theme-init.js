(function () {
        try {
          var t = localStorage.getItem("amk_portfolio_theme");
          if (t === "dark" || t === "light") {
            document.documentElement.setAttribute("data-theme", t);
          }
        } catch (e) {}
      })();
