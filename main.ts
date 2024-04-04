let numero = 0
input.onGesture(Gesture.Shake, function () {
    numero = randint(1, 6)
    if (numero == 1) {
        basic.showLeds(`
            . . . . .
            . . . . .
            . . # . .
            . . . . .
            . . . . .
            `)
        music.play(music.stringPlayable("C5 B A - - - - - ", 500), music.PlaybackMode.UntilDone)
    }
    if (numero == 2) {
        basic.showLeds(`
            # . . . .
            . . . . .
            . . . . .
            . . . . .
            . . . . #
            `)
        music.play(music.stringPlayable("C5 B A - - - - - ", 500), music.PlaybackMode.UntilDone)
    }
    if (numero == 3) {
        basic.showLeds(`
            # . . . .
            . . . . .
            . . # . .
            . . . . .
            . . . . #
            `)
        music.play(music.stringPlayable("C5 B A - - - - - ", 500), music.PlaybackMode.UntilDone)
    }
    if (numero == 4) {
        basic.showLeds(`
            # . . . #
            . . . . .
            . . . . .
            . . . . .
            # . . . #
            `)
        music.play(music.stringPlayable("C5 B A - - - - - ", 500), music.PlaybackMode.UntilDone)
    }
    if (numero == 5) {
        basic.showLeds(`
            # . . . #
            . . . . .
            . . # . .
            . . . . .
            # . . . #
            `)
        music.play(music.stringPlayable("C5 B A - - - - - ", 500), music.PlaybackMode.UntilDone)
    }
    if (numero == 6) {
        basic.showLeds(`
            # . . . #
            . . . . .
            # . . . #
            . . . . .
            # . . . #
            `)
        music.play(music.stringPlayable("C5 B A - - - - - ", 500), music.PlaybackMode.UntilDone)
    }
})
basic.forever(function () {
	
})
