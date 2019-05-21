var div = document.getElementById('parking-lot');
//car 1
div.innerHTML += "<img src='/static/img/car.png' width='160' height='120' style='position: absolute; left: 25px; top: 0px;' />";
//car 2
div.innerHTML += "<img src='/static/img/car.png' width='160' height='120' style='position: absolute; left: 25px; top: 100px;' />";
//car 3
div.innerHTML += "<img src='/static/img/car.png' width='160' height='120' style='position: absolute; left: 25px; top: 200px;' />";
//car 4
div.innerHTML += "<img src='/static/img/car.png' width='160' height='120' style='position: absolute; left: 500px; top: 0px;' />";
//car 5
div.innerHTML += "<img src='/static/img/car.png' width='160' height='120' style='position: absolute; left: 500px; top: 100px;' />";
//car 6
div.innerHTML += "<img src='/static/img/car.png' width='160' height='120' style='position: absolute; left: 500px; top: 200px;' />";

var points=[[0,0],[10,10],[100,100],[200,200]];
drawLines(points);


function drawLines(points) {
  var c = document.getElementById("myCanvas");
  var ctx = c.getContext("2d");
  for (var i = 0; i < points.length-1; i++) {
    ctx.beginPath();
    ctx.moveTo(points[i][0],points[i][1]);
    ctx.lineTo(points[i+1][0],points[i+1][1]);
    ctx.stroke();
  }
}
