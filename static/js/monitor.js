function show_picture(){
    
        
    setInterval(function () {
        
        $('#picture').attr("src","/picture");
        

    },2000);

}


$(document).ready( function () {
    
show_picture();


} );
