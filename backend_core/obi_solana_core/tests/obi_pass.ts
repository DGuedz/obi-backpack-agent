import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { ObiPass } from "../target/types/obi_pass";
import { assert } from "chai";

describe("obi_pass", () => {
  // Configure the client to use the local cluster.
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);

  const program = anchor.workspace.ObiPass as Program<ObiPass>;

  // Accounts
  const payer = provider.wallet as anchor.Wallet;
  
  // PDAs
  const [mintAuthorityPda] = anchor.web3.PublicKey.findProgramAddressSync(
    [Buffer.from("authority")],
    program.programId
  );

  const mintKeypair = anchor.web3.Keypair.generate();

  it("Is initialized!", async () => {
    try {
        const tx = await program.methods
        .initialize()
        .accounts({
            payer: payer.publicKey,
            mint: mintKeypair.publicKey,
            mintAuthority: mintAuthorityPda,
            systemProgram: anchor.web3.SystemProgram.programId,
            tokenProgram: anchor.utils.token.TOKEN_2022_PROGRAM_ID,
        })
        .signers([mintKeypair])
        .rpc();
        
        console.log("Initialize signature", tx);
    } catch (e) {
        console.error("Initialize failed:", e);
        throw e;
    }
  });

  it("Mints a license with payment", async () => {
    // Buyer
    const buyer = anchor.web3.Keypair.generate();
    // Airdrop SOL to buyer
    const signature = await provider.connection.requestAirdrop(buyer.publicKey, 2 * anchor.web3.LAMPORTS_PER_SOL);
    const latestBlockhash = await provider.connection.getLatestBlockhash();
    await provider.connection.confirmTransaction({ signature, ...latestBlockhash });

    // Treasury
    const treasury = anchor.web3.Keypair.generate();
    
    // Buyer Token Account (ATA)
    const buyerTokenAccount = anchor.utils.token.associatedAddress({
        mint: mintKeypair.publicKey,
        owner: buyer.publicKey,
    });

    const initialTreasuryBalance = await provider.connection.getBalance(treasury.publicKey);
    assert.equal(initialTreasuryBalance, 0);

    try {
        const tx = await program.methods
        .mintLicense()
        .accounts({
            buyer: buyer.publicKey,
            treasury: treasury.publicKey,
            mint: mintKeypair.publicKey,
            mintAuthority: mintAuthorityPda,
            buyerTokenAccount: buyerTokenAccount,
            systemProgram: anchor.web3.SystemProgram.programId,
            tokenProgram: anchor.utils.token.TOKEN_2022_PROGRAM_ID,
            associatedTokenProgram: anchor.utils.token.ASSOCIATED_PROGRAM_ID,
            rent: anchor.web3.SYSVAR_RENT_PUBKEY,
        })
        .signers([buyer])
        .rpc();

        console.log("Mint transaction signature", tx);

        // Verify Payment
        const finalTreasuryBalance = await provider.connection.getBalance(treasury.publicKey);
        console.log("Treasury Balance:", finalTreasuryBalance);
        assert.equal(finalTreasuryBalance, 1_000_000_000); // 1 SOL

        // Verify Token Minted
        const tokenBalance = await provider.connection.getTokenAccountBalance(buyerTokenAccount);
        assert.equal(tokenBalance.value.uiAmount, 1);
    } catch (e) {
        console.error("Mint failed:", e);
        throw e;
    }
  });
});
