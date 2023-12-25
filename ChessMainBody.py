
# Main driver file responsible for handling user input

import pygame as p
import ChessEngine
import SmartMoveFinder
from multiprocessing import Process, Queue


BOARD_WIDTH = BOARD_HEIGHT = 650
MOVE_LOG_PANEL_WIDTH = 350
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8
SQ_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15 # For animations later on
IMAGES = {}

def loadImages():
    pieces = ['wp', 'wR', 'wB', 'wN', 'wK', 'wQ', 'bp', 'bR', 'bB', 'bN', 'bK', 'bQ']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("ChessPieces/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))

def main():
    p.init()
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT), p.RESIZABLE)
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    moveLogFont = p.font.SysFont("Arial", 20, False, False)
    gs = ChessEngine.GameState()
    validMoves = gs.getValidMoves()
    moveMade = False # Flag variable for when a move is made
    animate = False # Flag variable for when we should animate a move
    loadImages() # Only happens once
    running = True
    sqSelected = () # No square is selected, keep track of the last click of the user (tuple: (row, col))
    playerClicks = []  # Keeps track of player clicks (two tuples [(X1, Y1) --> (X2, Y2)])
    gameOver = False
    playerOne = False # If a human is playing as white it will be true, if an AI is playing it will be false
    playerTwo = False # Same as above but for black
    AIThinking = False # Flag variable
    moveFinderProcess = None
    moveUndone = False
    while running:
        humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            # Mouse handler
            elif e.type == p.MOUSEBUTTONDOWN:
                if not gameOver:
                    location = p.mouse.get_pos()  # X and Y location
                    col = location[0]//SQ_SIZE
                    row = location[1]//SQ_SIZE
                    if sqSelected == (row, col) or col >= 8:  # User has clicked the same square twice
                        sqSelected = () # Deselects the square
                        playerClicks = [] # Clears the player's clicks
                    else:
                        sqSelected = (row, col)
                        playerClicks.append(sqSelected)  # Appends both the first and second clicks
                    if len(playerClicks) == 2 and humanTurn: # After the second click
                        move = ChessEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                        print(move.getChessNotation())
                        for i in range(len(validMoves)):
                            if move == validMoves[i]:
                                gs.makeMove(validMoves[i])
                                moveMade = True
                                animate = True
                                sqSelected = () # Resets the user's clicks
                                playerClicks = []
                        if not moveMade:
                            playerClicks = [sqSelected]
            # Key handler
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z: # Undo the move when 'z' is pressed
                    gs.undoMove()
                    moveMade = True
                    animate = False
                    gameOver = False
                    if AIThinking:
                        moveFinderProcess.terminate()
                        AIThinking = False
                    moveUndone = True

                if e.key == p.K_r: # Resets the board when 'r' is pressed
                    gs = ChessEngine.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False
                    gameOver = False
                    if AIThinking:
                        moveFinderProcess.terminate()
                        AIThinking = False
                    moveUndone = True

        # AI move finder
        if not gameOver and not humanTurn and not moveUndone:
            if not AIThinking:
                AIThinking = True
                print("Thinking...")
                returnQueue = Queue() # Used to pass data between threads
                moveFinderProcess = Process(target=SmartMoveFinder.findBestMove, args=(gs, validMoves, returnQueue))
                moveFinderProcess.start() # Calls findBestMove(gs, validMoves, returnQueue)

            if not moveFinderProcess.is_alive():
                print("Done thinking")
                AIMove = returnQueue.get()
                if AIMove is None:
                    AIMove = SmartMoveFinder.findRandomMove(validMoves)
                gs.makeMove(AIMove)
                moveMade = True
                animate = True
                AIThinking = False

        if moveMade:
            if animate:
                animateMove(gs.moveLog[-1], screen, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False
            moveUndone = False

        drawGameState(screen, gs, validMoves, sqSelected, moveLogFont)

        if gs.checkmate or gs.stalemate:
            gameOver = True
            drawEndGameText(screen, 'Stalemate' if gs.stalemate else 'Black wins by checkmate' if gs.whiteToMove else 'White wins by checkmate')

        clock.tick(MAX_FPS)
        p.display.flip()

def drawGameState(screen, gs, validMoves, sqSelected, moveLogFont):
    drawBoard(screen) # Draws the squares onto the board
    highlightSquares(screen, gs, validMoves, sqSelected)
    drawPieces(screen, gs.board)
    drawMoveLog(screen, gs, moveLogFont)


def drawBoard(screen):  # Top left square always has to be light
    global colors
    colors = [p.Color("white"), p.Color("dark green")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r+c) % 2)]
            p.draw.rect(screen, color, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

'''
Highlight squares and square selected and moves allowed for the selected piece 
'''
def highlightSquares(screen, gs, validMoves, sqSelected):
    if sqSelected != ():
        r, c = sqSelected
        if gs.board[r][c][0] == ('w' if gs.whiteToMove else 'b'): # selected square is a piece that can be moved
            # Highlight selected square
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)  # RGB settings 0 to 255, 0 = transparent, 255 = opaque
            s.fill(p.Color('blue'))
            screen.blit(s, (c*SQ_SIZE, r*SQ_SIZE))
            # Highlight moves from that square
            s.fill(p.Color('yellow'))
            for move in validMoves:
                if move.startRow == r and move.startCol == c:
                    screen.blit(s, (move.endCol*SQ_SIZE, move.endRow*SQ_SIZE))


def drawPieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--": # Not an empty square
                screen.blit(IMAGES[piece], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

def drawMoveLog(screen, gs, font):
    moveLogRect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color("black"), moveLogRect)
    moveLog = gs.moveLog
    moveTexts = [] # Modified later on
    for i in range(0, len(moveLog), 2):
        moveString = str(i//2 + 1) + ". " + str(moveLog[i]) + " "
        if i+1 < len(moveLog):
            moveString += str(moveLog[i+1]) + ""
        moveTexts.append(moveString)

    movesPerRow = 3
    padding = 5
    lineSpacing = 2
    textY = padding
    for i in range(0, len(moveTexts), movesPerRow):
        text = ""
        for j in range(movesPerRow):
            if i+j < len(moveTexts):
                text += moveTexts[i+j]
        textObject = font.render(text, True, 0, p.Color('white'))
        textLocation = moveLogRect.move(padding, textY)
        screen.blit(textObject, textLocation)
        textY += textObject.get_height() + lineSpacing


'''
Animating a move
'''
def animateMove(move, screen, board, clock):
    global colors
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    framesPerSquare = 10 # Controls the frame rate for each square
    frameCount = (abs(dR) + abs(dC)) * framesPerSquare
    for frame in range(frameCount + 1):
        r, c = (move.startRow + dR*frame/frameCount, move.startCol + dC*frame/frameCount)
        drawBoard(screen)
        drawPieces(screen, board)
        # Erase the moved piece from ending square
        color = colors[(move.endRow + move.endCol) % 2]
        endSquare = p.Rect(move.endCol*SQ_SIZE, move.endRow*SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, endSquare)
        # Draw the captured piece onto the rectangle
        if move.pieceCaptured != '--':
            if move.isEnpassantMove:
                enPassantRow = move.endRow + 1 if move.pieceCaptured[0] == 'b' else move.endRow - 1
                endSquare = p.Rect(move.endCol*SQ_SIZE, enPassantRow*SQ_SIZE, SQ_SIZE, SQ_SIZE)
            screen.blit(IMAGES[move.pieceCaptured], endSquare)
        # Draw the moving pieces
        screen.blit(IMAGES[move.pieceMoved], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)

def drawEndGameText(screen, text):
    font = p.font.SysFont("Helvetica", 32, True, False)
    textObject = font.render(text, 0, p.Color('Yellow'))
    textLocation = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - textObject.get_width() / 2, BOARD_HEIGHT / 2 - textObject.get_height() / 2)
    screen.blit(textObject, textLocation)
    textObject = font.render(text, 0, p.Color('Black'))
    screen.blit(textObject, textLocation.move(2, 2))



if __name__ == "__main__":
    main()
