function add_content(){
    const newContentName = prompt("Content Name");
    if(newContentName){
    window.location.replace(`/add/${newContentName}`)
    }
}
