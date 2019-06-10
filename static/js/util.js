// var div = document.getElementById('parking-lot');
//car 1
// div.innerHTML += "<img src='/static/img/car.png' width='160' height='120' style='position: absolute; left: 25px; top: 0px;' />";
// //car 2
// div.innerHTML += "<img src='/static/img/car.png' width='160' height='120' style='position: absolute; left: 25px; top: 100px;' />";
// //car 3
// div.innerHTML += "<img src='/static/img/car.png' width='160' height='120' style='position: absolute; left: 25px; top: 200px;' />";
// //car 4
// div.innerHTML += "<img src='/static/img/car.png' width='160' height='120' style='position: absolute; left: 500px; top: 0px;' />";
// //car 5
// div.innerHTML += "<img src='/static/img/car.png' width='160' height='120' style='position: absolute; left: 500px; top: 100px;' />";
// //car 6
// div.innerHTML += "<img src='/static/img/car.png' width='160' height='120' style='position: absolute; left: 500px; top: 200px;' />";



var pathes=[[[438,390],[438,250],[578,250]],
            [[438,390],[438,150],[578,150]],
            [[438,390],[438,50],[578,50]],
            [[438,390],[438,50],[98,50]],
            [[438,390],[438,150],[98,150]],
            [[438,390],[438,250],[98,250]]
            ];

function drawLines(points) {
  var c = document.getElementById("myCanvas");
  var ctx = c.getContext("2d");
  var gradient = ctx.createLinearGradient(0, 0, 500, 0);
  gradient.addColorStop("0", "magenta");
  gradient.addColorStop("0.5" ,"blue");
  gradient.addColorStop("1.0", "red");

  ctx.strokeStyle = gradient;
  ctx.lineWidth = 3;


  for (var i = 0; i < points.length-1; i++) {
    ctx.beginPath();
    ctx.moveTo(points[i][0],points[i][1]);
    ctx.lineTo(points[i+1][0],points[i+1][1]);
    ctx.stroke();
  }
}

function eraseLines() {
    var c = document.getElementById("myCanvas");
    var ctx = c.getContext("2d");
    ctx.clearRect(0, 0, 676, 682);
}


function drawPoint(point){
  var c= document.getElementById("myCanvas");
  var ctx=c.getContext("2d");
  ctx.fillRect(point[0],point[1],2,2);
}




function show_Parking_Fee() {
    $.ajax({
        url: '/carStatus',
        type: 'GET',
        success: function(data, textStatus, request) {
            $("#parkingTime").html(data['time']+' Min');
            $("#totalPrice").html('$'+data['time']*0.01);
            
        }
    });
}


function initial_Weather(){
    
$.ajax({
            url: '/weather',
            type: 'GET',
            success: function(data, textStatus, request) {
            $("#temp").html(data["main"]["temp"] + "<sup>°F</sup>");
            $("#weather").html(data["weather"][0]["main"]);
            var d = new Date();
            var n = d.getDay();
            $("#date").html(d.toDateString());
            $("#wind").html(data["wind"]["speed"] + "km/h");
            d = new Date(data["sys"]["sunrise"] * 1000);
            $("#sunrise").html(d.toTimeString());
            $("#pressure").html(data["main"]["pressure"] + "hPa");
            $("#weatherIcon").attr("src", "https://openweathermap.org/img/w/" + data["weather"][0]["icon"] + ".png");
            
            }
        });


}

function show_Weather() {
    setInterval(function() {
        $.ajax({
            url: '/weather',
            type: 'GET',
            success: function(data, textStatus, request) {
            $("#temp").html(data["main"]["temp"] + "<sup>°F</sup>");
            $("#weather").html(data["weather"][0]["main"]);
            var d = new Date();
            var n = d.getDay();
            $("#date").html(d.toDateString());
            $("#wind").html(data["wind"]["speed"] + "km/h");
            d = new Date(data["sys"]["sunrise"] * 1000);
            $("#sunrise").html(d.toTimeString());
            $("#pressure").html(data["main"]["pressure"] + "hPa");
            $("#weatherIcon").attr("src", "https://openweathermap.org/img/w/" + data["weather"][0]["icon"] + ".png");
            
            }
        });
			}, 300000);

}

function show_Gas() {
    $.ajax({
        url: '/gas',
        type: 'GET',
        success: function(data, textStatus, request) {
            $("#reg").html("Regular: " + data['details']['reg_price']);
            $("#mid").html("Mid-grade: " + data['details']['mid_price']);
            $("#pre").html("Premium: " + data['details']['pre_price']);
            
        }
    });
}


function show_parked_cars(){

    setInterval(function() {
        $.ajax({
            url: '/spotStatus',
            type: 'GET',
            success: function(data, textStatus, request) {
            var lots=data['status'];
            var lot = document.getElementById('parking-lot');
            console.log(lots);
            for (var i = 0; i < lots.length; i++) {
                if (lots[i]==1){
                    // lot.innerHTML += "<img src='/static/img/car.png' width='160' height='120' style='position: absolute; left:"+(25+475*Math.floor(i/3))+"px; top: "+(100*(i%3))+"px;' />";
                    $('#spot'+(i+1)).removeAttr("hidden");
                    console.log('#spot'+i);
                    
                }else{
                    $('#spot'+(i+1)).attr("hidden",'hidden');
                    
                    
                }
            };
            if(data['isIn']==1 && data['isParked']==0){
                var path=data['spot'];
                drawLines(pathes[path-1]);
            }
            }
        });
			}, 1000);

}


function show_car_status() {

    setInterval(function () {

        $.ajax({
        url: '/carStatus',
        type: 'GET',
        success: function(data, textStatus, request) {
            
            var start=new Date(data['start_time']);
            var span=(Date.now()-start)/1000
            
            if (data['status']==1 && data['spot_status']==0 && span<20){
                drawLines(pathes[data['spot']-1]);
            }else if (data['status']==1 && data['spot_status']==1)
            {
                eraseLines();
                //var lot = document.getElementById('parking-lot');
                //var i=data['spot']-1;
                //lot.innerHTML += "<img src='/static/img/car.png' width='160' height='120' style='position: absolute; left:"+(25+475*Math.floor(i/3))+"px; top: "+(100*(i%3))+"px;' />";
                
            }

        }
        });

    },1000);

}





function show_temp_humi() {

    setInterval(function () {

        $.ajax({
        url: '/temperature',
        type: 'GET',
        success: function(data, textStatus, request) {
            $("#Temp").html(data['temperature']+" <sup>°C</sup>");
            $("#Humi").html(data['humidity']+" %");

        }
        });

    },5000);

}





function show_record(){

    $.ajax({
        url: '/history',
        type: 'GET',
        success: function(data, textStatus, request) {
            

            for (var i =0;i<Object.keys(data).length;i++){

                record=data[i.toString()];

                var start=new Date(record['start_time']);
                var end=new Date(record['end_time']);
                var delta_time = Math.abs(end - start);
                var hours = (delta_time / (1000 * 60 * 60)).toFixed(1);

                $("#parkRecord").append("<tr><td>"+(i+1)+"</td>"+"<td>"+record['start_time']+"</td>"+"<td>"+record['end_time']+"</td>"+"<td>"+record['spot']+"</td>"+"<td>"+hours+" Hours</td>"+"<td>"+(hours)*record['rate']+"</td></tr>");
              


            }
            $('#myTable').DataTable();
        }
    });

}


function show_account(){
     
     
        
    setInterval(function () {
    $.ajax({
        url: '/carStatus',
        type: 'GET',
        success: function(data, textStatus, request) {
            
            var start=new Date(data['start_time']);
            var span=Math.floor((Date.now()-start)/(1000));
            var fee=(span*data['rate']).toFixed(1);
            var balance=data['balance'].toFixed(1);
            
            if (data['status']==1){
                $("#parkingTime").html(span+"  seconds");
                $("#balance").html(balance+'  dollars');
                $("#totalPrice").html(fee+'  dollars');
            }else{
                $("#parkingTime").html("0  seconds");
                $("#balance").html(balance+'  dollars');
                $("#totalPrice").html('0  dollars');
            
            }
            
            
            

        }
        });

    },2000);



}


$(document).ready( function () {
    
show_Parking_Fee();
//show_temp_humi();
show_Weather();
show_Gas();
show_parked_cars();
show_car_status();
show_record();
initial_Weather();
show_account();


} );
