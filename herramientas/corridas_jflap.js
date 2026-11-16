// Repite las corridas de jflap/simulacion/cadenas_de_prueba.txt con el
// simulador de JFLAP 7.1 (el mismo que usa Input > Multiple Run) y compara
// cada resultado con el esperado.
//
//   jjs -cp /ruta/JFLAP7.1.jar herramientas/corridas_jflap.js
//
// jjs (Nashorn) viene con Java 8. Se ejecuta desde la raíz del repositorio.

var Files = java.nio.file.Files, Paths = java.nio.file.Paths;
var carpeta = "jflap/simulacion/";
var lineas = Files.readAllLines(Paths.get(carpeta + "cadenas_de_prueba.txt"),
                                java.nio.charset.StandardCharsets.UTF_8);

var casos = {}, orden = [], actual = null;
for each (var linea in lineas) {
  linea = String(linea);
  // Los comentarios solo van en el encabezado: dentro de [comentario.jff] las
  // cadenas también empiezan con #.
  if (linea.trim() == "" || (actual === null && linea.startsWith("#"))) continue;
  var m = linea.match(/^\[(.+)\]$/);
  if (m) { actual = m[1]; casos[actual] = []; orden.push(actual); continue; }
  var partes = linea.trim().split(/\s+/);
  casos[actual].push({ cadena: partes[0], esperado: partes[1] });
}

var codec = new Packages.file.XMLCodec();
var total = 0, fallos = 0;
for each (var archivo in orden) {
  var automata = codec.decode(new java.io.File(carpeta + archivo), null);
  var ok = 0;
  for each (var c in casos[archivo]) {
    var simulador = new Packages.automata.fsa.FSAStepWithClosureSimulator(automata);
    var obtenido = simulador.simulateInput(c.cadena) ? "Accept" : "Reject";
    total++;
    if (obtenido == c.esperado) ok++;
    else { fallos++; print("  DIFERENTE  " + archivo + "  " + c.cadena + ": " + obtenido + " (esperado " + c.esperado + ")"); }
  }
  print(archivo + ": " + ok + "/" + casos[archivo].length);
}
print(total + " cadenas, " + fallos + " diferencias");
java.lang.System.exit(fallos ? 1 : 0);
